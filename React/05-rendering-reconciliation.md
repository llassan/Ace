# Rendering & Reconciliation

React's rendering model is deceptively simple on the surface but contains layers of nuance that separate senior engineers from mid-level ones. Mastering the two-phase model, Fiber's scheduler, and the precise rules for re-renders lets you debug "why did this component re-render?" with surgical precision — the question that defines senior React interviews.

---

## The Two Phases: Render vs Commit

### Q: What are the two phases of a React update, and why does this distinction matter?

**Mental model:** React splits work into a *description* phase (render) and an *execution* phase (commit). This separation is what makes Concurrent React possible.

**Render phase** — React calls your component functions and hooks, building a tree of React elements. It is pure: no DOM mutations, no observable side effects. React can pause, abandon, or restart render work at any time without affecting what the user sees.

**Commit phase** — React takes the computed element tree, diffs it against the current DOM (using the fiber work-in-progress tree), and applies mutations. This phase is synchronous and cannot be interrupted.

```tsx
// This component is called during render phase — must be pure
function UserCard({ userId }: { userId: string }) {
  // Reading state, computing JSX — fine
  const [expanded, setExpanded] = useState(false);
  const label = expanded ? "Collapse" : "Expand";

  // ❌ This would be a side effect in render phase — wrong
  // document.title = userId;

  return <button onClick={() => setExpanded(e => !e)}>{label}</button>;
}
```

**Why render must be pure:** In Concurrent Mode, React may call your component multiple times before ever committing. If render had side effects (network calls, DOM mutations, subscriptions), those would fire multiple times or at unexpected times. This is why `useEffect` exists — it runs after commit, safely.

> 💡 Senior insight: StrictMode deliberately double-invokes render functions in development to surface render-phase side effects. If your component behaves differently on the second call, you have a purity bug.

**Follow-ups they'll ask:**
- "What happens if you throw during render?" React unwinds to the nearest error boundary and continues committing the fallback.
- "Can useLayoutEffect run before the browser paints?" Yes — layout effects run synchronously after DOM mutations but before the browser paints. Passive effects (`useEffect`) run after paint.

---

## Virtual DOM: The Correct Mental Model

### Q: What is the Virtual DOM, and why is "it's faster than the real DOM" wrong?

**Mental model:** The virtual DOM is a plain JavaScript object tree that *describes* what the UI should look like. It is a programming model, not a performance hack.

```tsx
// What JSX compiles to — a plain object (React element)
const element = React.createElement("button", { className: "btn" }, "Click me");
// { type: "button", props: { className: "btn", children: "Click me" }, ... }
```

**Why "faster than DOM" is a myth:** Creating virtual DOM nodes is not free. Every render allocates JavaScript objects. The actual DOM read/write operations that cause reflow are expensive — but React does not magically eliminate those. React *batches* and *minimizes* DOM mutations, which is the real win. A vanilla JS app that makes the same minimal DOM mutations would be equally fast.

**Three distinct concepts:**

| Concept | What it is |
|---|---|
| React element | Plain JS object `{ type, props, key, ref }` returned by JSX |
| Fiber node | Internal React object tracking component state, effects, work priority, parent/child links |
| DOM node | Actual browser element created during commit |

One component can produce many elements across renders. A fiber persists across renders (it is the unit of incremental work). The DOM node is created once and mutated.

> 💡 Senior insight: React elements are *immutable descriptions*. Fibers are *mutable work records*. Conflating them leads to confusion about when state is preserved vs destroyed.

⚠️ Gotcha: `React.memo` compares *props* (the element's props object), not the element itself. Two renders of the same element type with identical props can still trigger a re-render if a prop reference changed.

---

## React Fiber: The Scheduler Architecture

### Q: Why was Fiber introduced, and what problem does it solve?

**Mental model:** Pre-Fiber React (the "stack reconciler") did a depth-first synchronous traversal of the entire component tree on every update. It could not be paused. A slow tree would block the main thread and freeze the UI.

Fiber reimagines the reconciler as a linked list of units of work that can be paused between nodes, yielding control back to the browser's event loop.

```
Fiber node (simplified):
{
  type: FunctionComponent | string | null,
  stateNode: DOM node | class instance | null,
  child: Fiber | null,        // first child
  sibling: Fiber | null,      // next sibling
  return: Fiber | null,       // parent
  alternate: Fiber | null,    // the other tree (double buffer)
  lanes: Lanes,               // priority bitmask
  pendingProps: any,
  memoizedProps: any,
  memoizedState: Hook | null, // linked list of hook state
}
```

**Double buffering (current vs work-in-progress):**

React maintains two fiber trees simultaneously. The *current* tree reflects what is on screen. When an update starts, React clones nodes into a *work-in-progress* tree and builds on that. On commit, the work-in-progress tree becomes the new current tree by pointer swap — a single atomic operation.

This is why state reads always return the committed value: you are reading from the current tree, not the partially-built work-in-progress tree.

**Priority lanes (high level):**

React 18 uses a bitmask of "lanes" to categorize work by urgency. High-priority work (user input, discrete events) interrupts lower-priority work (deferred transitions, background data fetching).

```tsx
// startTransition marks work as low-priority (transition lane)
import { startTransition, useState } from "react";

function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<string[]>([]);

  function handleInput(e: React.ChangeEvent<HTMLInputElement>) {
    const value = e.target.value;
    setQuery(value); // urgent: keep input responsive

    startTransition(() => {
      setResults(expensiveFilter(value)); // non-urgent: can be interrupted
    });
  }

  return <input value={query} onChange={handleInput} />;
}
```

> 💡 Senior insight: Lanes are a bitmask, not a queue. React can process multiple lanes in a single pass when they share priority. This is fundamentally different from a FIFO task queue.

**Follow-ups they'll ask:**
- "What is React Scheduler?" A separate package (`scheduler`) that coordinates time-slicing using `MessageChannel` or `setTimeout` for yielding to the browser event loop.
- "Does Fiber mean React is always concurrent?" No. Without Concurrent Mode features (`startTransition`, `Suspense`, etc.), React still commits synchronously. Fiber enables concurrency; it does not enforce it.

---

## Reconciliation: The Diffing Heuristics

### Q: How does React's O(n) diffing work, and what assumptions does it make?

**Mental model:** A general tree diff algorithm is O(n³). React achieves O(n) by making two aggressive assumptions: components of different types produce fundamentally different trees, and stable keys identify elements across renders.

**Same type → update:**

```tsx
// Before update
<Button color="blue" />
// After update
<Button color="red" />
// React keeps the fiber, updates props — state is preserved
```

**Different type → remount:**

```tsx
// Before
<Input value={text} />
// After — type changed (even if visually similar)
<Textarea value={text} />
// React destroys Input's fiber (and its state!), mounts fresh Textarea
```

**Why type identity matters — the classic nested-definition bug:**

```tsx
// ❌ BUG: ParentComponent redefines InnerList on every render
function ParentComponent() {
  // This function is recreated on each render — new reference, new "type"
  function InnerList({ items }: { items: string[] }) {
    return <ul>{items.map(i => <li key={i}>{i}</li>)}</ul>;
  }

  return <InnerList items={["a", "b", "c"]} />;
}
```

On every parent render, `InnerList` is a brand-new function reference. React sees a *different type* at that position in the tree and remounts it. Any state inside `InnerList` is destroyed on every parent render.

```tsx
// ✅ CORRECT: Define outside the parent — stable reference
function InnerList({ items }: { items: string[] }) {
  return <ul>{items.map(i => <li key={i}>{i}</li>)}</ul>;
}

function ParentComponent() {
  return <InnerList items={["a", "b", "c"]} />;
}
```

> 💡 Senior insight: This bug also appears with inline anonymous components in JSX: `render={() => <div>...</div>}` as a prop creates a new component type each time. Use stable references.

⚠️ Gotcha: The heuristic applies *per tree position*. If the type changes at position 0, React does not compare it to position 1. It destroys position 0's subtree entirely.

**Follow-ups they'll ask:**
- "What is the algorithmic complexity of key-based list diffing?" Still O(n) over the list length — React uses a map from key to fiber for O(1) lookups within the list.

---

## Keys: List Diffing, Index Pitfalls, and the Remount Trick

### Q: What exactly do keys do, and when does using index-as-key break things?

**Mental model:** Keys are hints to the reconciler: "this element represents the same conceptual item across renders, regardless of position." Without keys, React diffs by position. With keys, React diffs by identity.

**Index-as-key concrete bug:**

```tsx
// ❌ Index as key — inserting at the front causes cascading state loss
function TodoList() {
  const [todos, setTodos] = useState([
    { id: 1, text: "Buy milk" },
    { id: 2, text: "Write tests" },
  ]);

  return (
    <ul>
      {todos.map((todo, index) => (
        // key=index: after prepend, "Buy milk" maps to index 0 → same fiber
        // "Write tests" maps to index 1 → same fiber
        // The NEW item has no previous fiber — it mounts fresh
        // BUT the fibers at 0 and 1 retain OLD state (e.g. checked status)
        <TodoItem key={index} todo={todo} />
      ))}
    </ul>
  );
}

// ✅ Stable ID as key
{todos.map(todo => <TodoItem key={todo.id} todo={todo} />)}
```

**When index-as-key is safe:** Static lists that never reorder or add/remove items in the middle. Example: a fixed set of tab panels.

**Key as a deliberate remount tool:**

```tsx
// Reset a form by changing its key — forces full remount, clearing all state
function UserProfile({ userId }: { userId: string }) {
  return <ProfileForm key={userId} userId={userId} />;
}
// When userId changes, ProfileForm unmounts entirely and remounts fresh
// Cleaner than managing reset logic inside ProfileForm with useEffect
```

> 💡 Senior insight: The "key as reset" pattern is the idiomatic React way to reset derived state or child component state without lifting it up or using imperative refs.

⚠️ Gotcha: Keys must be unique *among siblings*, not globally. `key="1"` in one list and `key="1"` in a separate sibling list are fine — they are in different reconciliation contexts.

---

## Why Did My Component Re-render?

### Q: What are the precise rules that trigger a component re-render?

**Mental model:** A component re-renders when React decides it *might* need to produce different output. The trigger sources are:

1. **Its own state changed** — via `setState`, `useReducer` dispatch
2. **Its parent re-rendered** — React re-renders all children by default, even if props are unchanged
3. **A consumed context value changed** — any component calling `useContext(Ctx)` re-renders when `Ctx`'s value reference changes
4. **A hook it uses schedules a re-render** — e.g., `useSyncExternalStore`, custom hooks calling `useState` internally

**The #1 culprit: new object/function identity on every parent render:**

```tsx
// ❌ New object reference every render — memo is useless
function Parent() {
  const [count, setCount] = useState(0);

  // New reference on every Parent render
  const config = { timeout: 5000, retries: 3 };
  const handleClick = () => console.log("clicked");

  return <ExpensiveChild config={config} onClick={handleClick} />;
}

// ✅ Stable references
function Parent() {
  const [count, setCount] = useState(0);

  const config = useMemo(() => ({ timeout: 5000, retries: 3 }), []);
  const handleClick = useCallback(() => console.log("clicked"), []);

  return <ExpensiveChild config={config} onClick={handleClick} />;
}
```

**Diagnosing with React DevTools Profiler:**

1. Open React DevTools → Profiler tab
2. Record an interaction
3. Click a flamegraph bar — it shows *why* that component rendered: "Props changed", "State changed", "Context changed", "Hooks changed"
4. "Props changed" + identical-looking props → a reference identity issue

**why-did-you-render library:**

```tsx
// In development setup
import whyDidYouRender from "@welldone-software/why-did-you-render";
import React from "react";

whyDidYouRender(React, { trackAllPureComponents: true });

// On any component you want to monitor:
ExpensiveChild.whyDidYouRender = true;
// Console will log: "Re-rendered due to props.config changing: {} !== {}"
```

> 💡 Senior insight: Context is the most surprising re-render source. A context value that is an object literal `<Ctx.Provider value={{ user, theme }}>` creates a new reference on every Provider render, re-rendering *all* consumers. Fix: memoize the value or split into separate contexts.

⚠️ Gotcha: React does not bail out before calling a component when the parent re-renders (unless `memo` is used). "Re-render" means "React calls the function again" — it does not necessarily mean "DOM updated". A re-render that produces identical output causes no DOM mutations.

**Follow-ups they'll ask:**
- "Does forceUpdate still exist?" In class components, yes. In function components, the pattern `const [, forceRender] = useReducer(x => x + 1, 0)` is equivalent but rarely needed.

---

## Render Bailouts: memo, Object.is, and Skipping Children

### Q: When does React skip re-rendering a component or its children?

**Mental model:** React has two bailout mechanisms: one for the current component (via `Object.is` comparison on new state), and one for component subtrees (via `React.memo`).

**Object.is bailout:**

```tsx
function Counter() {
  const [count, setCount] = useState(0);

  // Clicking this when count is already 0 → Object.is(0, 0) === true
  // React bails out — no re-render, no children re-render
  return <button onClick={() => setCount(0)}>Reset</button>;
}
```

React uses `Object.is` (not `===`) for the comparison. Key difference: `Object.is(NaN, NaN)` is `true`, `Object.is(0, -0)` is `false`.

**React.memo — what it does and does not do:**

```tsx
// memo wraps the component and shallowly compares each prop
const ExpensiveList = React.memo(function ExpensiveList({
  items,
  onSelect,
}: {
  items: string[];
  onSelect: (item: string) => void;
}) {
  return (
    <ul>
      {items.map(item => (
        <li key={item} onClick={() => onSelect(item)}>{item}</li>
      ))}
    </ul>
  );
});

// memo does NOT help if:
// - items is a new array reference each render (even with same contents)
// - onSelect is a new function reference each render
```

**Shallow comparison means:** `Object.is(prevProp, nextProp)` for each key. Arrays and objects fail this if they are new references, regardless of contents.

**Custom comparator:**

```tsx
const Item = React.memo(
  function Item({ data }: { data: { id: string; value: number } }) {
    return <div>{data.value}</div>;
  },
  (prev, next) => prev.data.id === next.data.id && prev.data.value === next.data.value
);
```

> 💡 Senior insight: `memo` is not free. It adds a prop-comparison cost on every parent render. For cheap components, memo can be *slower* than just re-rendering. Profile before adding memo indiscriminately.

⚠️ Gotcha: Even with memo, a component re-renders when its own state or consumed context changes. Memo only blocks the *parent-driven* re-render.

---

## Batching: Legacy and React 18 Automatic Batching

### Q: What is batching, and how did React 18 change it?

**Mental model:** Batching means React groups multiple state updates triggered in the same event handler into a single re-render. Without batching, each `setState` call would trigger a separate render.

**Legacy behavior (React 17 and below):**

```tsx
// In React 17, batching only worked inside React event handlers
// In async callbacks, each setState triggered a separate render
fetchUser().then(user => {
  setUser(user);    // render 1
  setLoading(false); // render 2
});
```

**React 18 automatic batching everywhere:**

```tsx
// React 18: batched automatically, even in setTimeout, promises, native events
fetchUser().then(user => {
  setUser(user);     // \
  setLoading(false); //  → single render
  setError(null);    // /
});
```

**flushSync escape hatch:**

```tsx
import { flushSync } from "react-dom";

function handleClick() {
  flushSync(() => {
    setCount(c => c + 1); // commits immediately — DOM updated
  });
  // At this point, the DOM reflects the new count
  // Useful for measuring DOM before next state update
  flushSync(() => {
    setFlag(true); // second synchronous commit
  });
}
```

> 💡 Senior insight: `flushSync` is a performance escape hatch, not a correctness tool. Overusing it defeats automatic batching. Common legitimate use: reading DOM measurements that depend on just-set state.

**Follow-ups they'll ask:**
- "What about `unstable_batchedUpdates`?" It still works in React 18 but is largely unnecessary since automatic batching covers all cases. It exists for library authors supporting both React 17 and 18.

---

## Concurrent Features: Transitions, Deferred Values, and Tearing

### Q: What does "concurrent React" mean, and how do transitions and deferred values work?

**Mental model:** Concurrent React means React can work on multiple versions of the UI simultaneously, interrupting lower-priority work when higher-priority updates arrive. The user always sees a consistent, committed version — never a partially-rendered intermediate state.

**startTransition / useTransition:**

```tsx
import { useTransition, useState } from "react";

function SearchPage() {
  const [isPending, startTransition] = useTransition();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Result[]>([]);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setQuery(e.target.value); // urgent — input stays responsive

    startTransition(() => {
      // Non-urgent — React can interrupt and restart this
      // if the user types again before it finishes
      setResults(search(e.target.value));
    });
  }

  return (
    <>
      <input value={query} onChange={handleChange} />
      {isPending ? <Spinner /> : <ResultsList results={results} />}
    </>
  );
}
```

**useDeferredValue — deferred without a transition boundary:**

```tsx
import { useDeferredValue, memo } from "react";

function SearchResults({ query }: { query: string }) {
  const deferredQuery = useDeferredValue(query);
  // deferredQuery lags behind query — React renders with stale value first
  // then schedules a low-priority render with the new value
  const isStale = deferredQuery !== query;

  return (
    <div style={{ opacity: isStale ? 0.6 : 1 }}>
      <ExpensiveList query={deferredQuery} />
    </div>
  );
}
```

**Tearing and useSyncExternalStore:**

Tearing is a concurrent-mode problem: if an external store (e.g., Redux, Zustand) updates mid-render, different components that read the store at different points in the render phase could see different values — a torn, inconsistent UI.

```tsx
// useSyncExternalStore forces synchronous reads to prevent tearing
import { useSyncExternalStore } from "react";

function useStore<T>(selector: (state: AppState) => T): T {
  return useSyncExternalStore(
    store.subscribe,        // subscribe to external store
    () => selector(store.getState()), // get current snapshot
    () => selector(serverSnapshot)   // server snapshot (SSR)
  );
}
```

> 💡 Senior insight: `useSyncExternalStore` is what Redux and Zustand use internally in React 18. If you are building a custom store, this is the correct primitive — not `useEffect` + `useState`.

**Suspense as a rendering primitive:**

```tsx
// Suspense catches thrown promises during render (data fetching with use())
import { Suspense, use } from "react"; // React 19

function UserProfile({ userPromise }: { userPromise: Promise<User> }) {
  const user = use(userPromise); // throws Promise if not resolved — Suspense catches it
  return <div>{user.name}</div>;
}

function App() {
  const userPromise = fetchUser("123");
  return (
    <Suspense fallback={<Skeleton />}>
      <UserProfile userPromise={userPromise} />
    </Suspense>
  );
}
```

**Follow-ups they'll ask:**
- "Can you nest Suspense boundaries?" Yes — React uses the nearest ancestor Suspense boundary. Fine-grained boundaries allow partial loading UIs.
- "What is the difference between startTransition and useDeferredValue?" Transition wraps the *update source* (setter call). DeferredValue wraps the *consumed value* in a child that you cannot control directly.

---

## Commit Phase and Effect Timing

### Q: What is the ordering of effects after a commit, and why does it matter?

**Mental model:** Effects run after the commit phase, but in a specific order that mirrors the component tree depth.

```
Render phase → Commit phase (mutations) → Layout effects → Browser paint → Passive effects
```

**Precise ordering:**

```tsx
function Parent() {
  useLayoutEffect(() => {
    console.log("2: Parent layout");
    return () => console.log("5: Parent layout cleanup");
  });
  useEffect(() => {
    console.log("4: Parent effect");
    return () => console.log("7: Parent effect cleanup");
  });
  return <Child />;
}

function Child() {
  useLayoutEffect(() => {
    console.log("1: Child layout");  // children first, depth-first
    return () => console.log("6: Child layout cleanup");
  });
  useEffect(() => {
    console.log("3: Child effect");
    return () => console.log("8: Child effect cleanup");
  });
  return <div />;
}

// Console order on mount:
// 1: Child layout
// 2: Parent layout
// [browser paints]
// 3: Child effect
// 4: Parent effect

// Console order on unmount:
// 5: Parent layout cleanup
// 6: Child layout cleanup
// 7: Parent effect cleanup
// 8: Child effect cleanup
```

**When to use useLayoutEffect:**

Use it when you need to read DOM layout (dimensions, scroll position) and synchronously apply changes before the browser paints — preventing a visible flash.

```tsx
function Tooltip({ anchorRef }: { anchorRef: RefObject<HTMLElement> }) {
  const tooltipRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    // Synchronously read and apply position — user never sees misplaced tooltip
    const anchorRect = anchorRef.current!.getBoundingClientRect();
    tooltipRef.current!.style.top = `${anchorRect.bottom}px`;
  });

  return <div ref={tooltipRef} className="tooltip" />;
}
```

> 💡 Senior insight: useLayoutEffect blocks the browser paint. If your measurement/mutation is slow, it directly impacts Time to First Paint. Prefer useEffect unless you have a concrete flash/flicker problem.

⚠️ Gotcha: useLayoutEffect in SSR causes a hydration mismatch warning because it cannot run on the server. Use `useEffect` for SSR-safe code, or conditionally suppress with `typeof window !== 'undefined'` checks (carefully).

---

## StrictMode Double Render

### Q: Why does StrictMode call your component twice in development?

**Mental model:** StrictMode exists to surface non-obvious bugs by deliberately exercising behaviors that Concurrent Mode may produce in production.

**What StrictMode does in development:**
- Invokes render functions twice (components, `useState` initializers, `useMemo` factory, `useReducer` reducers)
- Invokes effects twice (`useEffect` setup → cleanup → setup)
- Warns about deprecated APIs

**Purpose of double render:** If a render function has side effects (mutations, network calls, subscriptions), the second call reveals the bug in development rather than letting it fail unpredictably in Concurrent Mode production.

```tsx
// Bug revealed by StrictMode double render
function BadComponent() {
  // This push happens twice in dev — array grows by 2, not 1
  // In production without concurrent features, it might only happen once
  globalList.push("item");
  return <div>{globalList.length}</div>;
}
```

**Purpose of double effect:** Verifies that cleanup functions properly undo setup, since concurrent React may mount → unmount → remount components (e.g., when preserving offscreen state in the future).

```tsx
// Correct — cleanup undoes setup completely
useEffect(() => {
  const sub = store.subscribe(listener);
  return () => sub.unsubscribe(); // ✅ symmetric
}, []);

// Bug — double-mounting leaves two subscriptions after cleanup fails
useEffect(() => {
  store.subscribe(listener); // ❌ no cleanup — double subscription in StrictMode
}, []);
```

> 💡 Senior insight: StrictMode's double-effect behavior in React 18 is the source of the "useEffect fires twice on mount" confusion. It is intentional and correct. Your cleanup must be symmetric with your setup.

---

## Common Rendering Performance Traps

### Q: What are the most common rendering performance mistakes you have seen, and how do you reason about them?

**Mental model:** Before optimizing, measure. Most render performance problems fall into three categories: unnecessary re-renders, expensive render work, and unthrottled commit-phase reads.

**Trap 1: Context with object value (covered above) — splits context by update frequency:**

```tsx
// Split high-frequency (theme) from low-frequency (user) context
const ThemeContext = createContext<Theme>(defaultTheme);
const UserContext = createContext<User | null>(null);
// Consumers of UserContext do not re-render when theme changes
```

**Trap 2: Expensive computation inline in render:**

```tsx
// ❌ Runs on every render
function DataTable({ rows }: { rows: Row[] }) {
  const sorted = rows.slice().sort(compareFn); // O(n log n) every render
  return <Table data={sorted} />;
}

// ✅ Recomputes only when rows changes
function DataTable({ rows }: { rows: Row[] }) {
  const sorted = useMemo(() => rows.slice().sort(compareFn), [rows]);
  return <Table data={sorted} />;
}
```

**Trap 3: Unstable default prop values:**

```tsx
// ❌ New empty array reference on every render when items not provided
function List({ items = [] }: { items?: string[] }) { ... }

// ✅ Stable default outside component
const EMPTY: string[] = [];
function List({ items = EMPTY }: { items?: string[] }) { ... }
```

**Trap 4: Reading layout in useEffect causing forced layout:**

```tsx
// ❌ Forces synchronous layout calculation mid-effect
useEffect(() => {
  const height = ref.current.offsetHeight; // triggers layout
  setAdjustedHeight(height + 20); // triggers re-render → another layout
});

// ✅ Use useLayoutEffect when reading DOM geometry that drives state
useLayoutEffect(() => {
  const height = ref.current!.offsetHeight;
  setAdjustedHeight(height + 20);
}, []);
```

**Trap 5: Missing keys causing full list remounts:**

When keys are absent from a dynamic list, React diffs by index position. Insertions at the beginning remount all existing items, destroying their state and running full mount effects.

> 💡 Senior insight: The Profiler flamegraph's "Render duration" bars are your guide. A wide bar means expensive render work (move it to useMemo or virtualize). Many thin bars across unrelated components means a context or state-lifting issue (split context or move state down).

For advanced virtualization, code splitting, and Web Worker patterns, see file 07 on performance optimization.

---

## Rapid-Fire

**Q: Can React render without committing?**
Yes. In Concurrent Mode, React may render (call component functions) and then discard the work-in-progress tree if a higher-priority update arrives.

**Q: What does `Object.is` return for two `[]` literals?**
`false` — they are different object references.

**Q: Does `useMemo` guarantee memoization?**
No. React may discard memoized values in low-memory situations (future behavior). It is an optimization hint, not a guarantee.

**Q: What triggers a context consumer to re-render?**
The context *value* reference changing at the nearest `Provider`. `React.memo` does not block context-driven re-renders.

**Q: Can you call hooks inside `startTransition`?**
No — hooks must be called at the top level of a component function, not inside callbacks.

**Q: What is the difference between bailout and no-op render?**
Bailout: React skips calling the component entirely (via memo or Object.is). No-op render: React calls the component, produces identical output, and skips DOM mutations — more expensive than a bailout.

**Q: Does changing a key always cause a full remount?**
Yes. A key change means a different identity to React — the previous fiber is unmounted (effects cleaned up) and a fresh fiber is mounted.

**Q: What fires during the "passive effects" phase?**
`useEffect` callbacks and their cleanup functions from the previous render.

---

## Red Flags

- Defining components inside other components ("I do it to share state easily") — causes remount on every parent render, one of the most common React performance bugs.
- "I added `memo` everywhere to make the app faster" without profiling — memo has overhead; untargeted use can slow down simple components.
- "I use `useEffect` to sync two pieces of state" — almost always a derived state problem; compute at render time instead.
- "The double render in StrictMode is a bug so I wrapped it in a ref check" — this hides real bugs; fix the underlying side effect in render.
- Putting the entire app state in a single context — guarantees that every state change re-renders every consumer.
- "I use `useLayoutEffect` for all my effects to be safe" — blocks paint on every effect; use it only for DOM measurement that must be synchronous.
- Not providing `key` props on dynamically-rendered lists ("React works fine without them") — silently corrupts state on reorder and causes full subtree remounts.
- "I fixed the stale closure by removing the ESLint exhaustive-deps rule" — the linter is correct; disabling it hides dependency bugs that will surface as intermittent state bugs in production.
