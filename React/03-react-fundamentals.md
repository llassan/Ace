# React Fundamentals

Senior interviews probe fundamentals not to check if you can define them, but to see whether you understand *why* they work the way they do and can defend design decisions under pressure. Interviewers at the lead level expect you to connect each concept to trade-offs, performance implications, and real bugs you would have introduced without that understanding. Knowing the API is table stakes — knowing the reasoning behind it is what separates candidates.

---

## What React Actually Is

### "React is a library, not a framework" — why does that distinction matter in an interview?

**Mental model:** A framework owns your architecture and calls your code (inversion of control). A library is a tool you call. React owns one thing: efficiently updating the DOM to match a description of UI you provide. Routing, data-fetching, state management, form handling — those are your problem.

**Trade-off this creates:**

- Freedom: compose the exact stack you need (Zustand + React Router + React Query vs Redux + RTK Query).
- Cost: every project must make those choices, leading to ecosystem fragmentation and "decision fatigue" for teams.
- At scale: frameworks built *on top of* React (Next.js, Remix) add the missing opinions and re-introduce that inversion of control selectively.

**Declarative vs imperative:**

Imperative — you describe *how* to get there:
```ts
const el = document.getElementById('count');
el.textContent = String(count + 1);
count++;
```

Declarative — you describe *what* the UI should look like at any given moment:
```tsx
function Counter() {
  const [count, setCount] = React.useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

React figures out *how* to make the DOM match. You never touch the DOM directly.

**"UI as a function of state":**
```
UI = f(state)
```
Given the same state, the same UI is produced. This is why React components are ideally pure functions — predictable, testable, and composable. Side effects (data fetching, subscriptions) are explicitly isolated so they don't break that contract.

> 💡 Senior insight: The purity contract is why StrictMode double-invokes render in development — it surfaces functions that accidentally depend on side effects during render.

**Follow-ups they'll ask:**
- What does React *not* handle that a full framework does?
- How does "UI = f(state)" break down in practice, and how do you repair it?
- Why is declarative easier to reason about at scale?

---

## JSX

### What does JSX actually compile to, and why should a senior engineer care?

JSX is syntactic sugar. Since React 17, the automatic JSX runtime is the default transform:

```tsx
// You write:
const el = <h1 className="title">Hello</h1>;

// Babel/TS compiles to (automatic runtime):
import { jsx as _jsx } from 'react/jsx-runtime';
const el = _jsx('h1', { className: 'title', children: 'Hello' });

// Before React 17 (classic runtime):
const el = React.createElement('h1', { className: 'title' }, 'Hello');
```

**Why it matters:**

- Pre-17 you needed `import React from 'react'` in every file, or createElement was undefined. Now you don't.
- Understanding the compiled output explains why you can't use statements (like `if` blocks) inside JSX — JSX is an *expression* that resolves to a function call.
- It also explains why returning multiple siblings requires a wrapper: `createElement` takes one root element.

### Expressions vs statements, fragments, and the `0 &&` trap

```tsx
// Expressions work — they produce a value:
const el = <p>{isLoggedIn ? 'Hi' : 'Log in'}</p>;

// Statements do NOT work inside {}:
// const el = <p>{if (x) { return 'y' }}</p>; // syntax error

// Fragments avoid adding DOM nodes:
function Row() {
  return (
    <>
      <td>First</td>
      <td>Last</td>
    </>
  );
}

// ⚠️ Classic conditional rendering bug:
// 0 is falsy but React renders it as the string "0"
const count = 0;
return <div>{count && <Badge />}</div>; // renders "0" in the DOM!

// Fix: coerce to boolean
return <div>{count > 0 && <Badge />}</div>;
// or
return <div>{!!count && <Badge />}</div>;
// or use ternary:
return <div>{count ? <Badge /> : null}</div>;
```

> ⚠️ Gotcha: `null`, `undefined`, and `false` render nothing. The number `0` and empty string `""` *do* render. This asymmetry bites even experienced engineers.

### Keys: the short version (deep dive in file 05)

Keys tell React which element in a list corresponds to which element in the previous render. Without stable keys, React falls back to index-based reconciliation and produces incorrect diffs.

**Index-as-key bug — concrete reordering example:**

```tsx
// items = ['Apple', 'Banana', 'Cherry']
// User removes 'Apple' → items = ['Banana', 'Cherry']

// With index keys:
// Before: key=0 Apple, key=1 Banana, key=2 Cherry
// After:  key=0 Banana, key=1 Cherry
// React sees: key=0 changed text (updates), key=2 removed (destroys)
// If each item had local state (e.g. an input), that state shifts to the wrong item.

// Correct — use a stable unique ID:
items.map(item => <Item key={item.id} data={item} />);
```

See **file 05 — Rendering Internals** for reconciliation depth.

**Follow-ups they'll ask:**
- When is it acceptable to use index as key?
- What happens to component state when a key changes?
- Why can't keys be read as props inside the child component?

---

## Components

### Function components vs class components — why did functions win?

**Class components:**
```tsx
class Greeting extends React.Component<{ name: string }, { count: number }> {
  state = { count: 0 };
  render() {
    return <h1>Hello {this.props.name}, clicked {this.state.count}</h1>;
  }
}
```

**Function components (modern):**
```tsx
function Greeting({ name }: { name: string }) {
  const [count, setCount] = React.useState(0);
  return <h1>Hello {name}, clicked {count}</h1>;
}
```

**Why functions won:**

1. **Closures capture props/state at render time** — no stale `this` bugs.
2. **Hooks enable composable stateful logic** — extracting logic from a class requires HOCs or render props, both of which add nesting and complexity.
3. **Less boilerplate** — no constructors, no binding, no lifecycle method sprawl.
4. **Better for the compiler** — React Compiler (React 19 / experimental) can optimize pure functions far more aggressively than classes.

> 💡 Senior insight: The `this` problem in classes is not just ergonomic — it's a source of subtle bugs. A class render method always reads the *latest* this.props, meaning event handlers captured in closures inside render could read stale values depending on when they close over `this`. Function components with hooks give you a clear mental model: each render is a snapshot.

### Composition over inheritance

React deliberately provides no class extension mechanism beyond `React.Component` itself. The React team has stated that composition always produces more flexible code than inheritance for UI.

```tsx
// Inheritance (anti-pattern in React):
class FancyButton extends Button { /* ... */ }

// Composition (idiomatic):
function FancyButton({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button className="fancy" {...props}>
      {children}
    </button>
  );
}
```

### Container/presentational — and why that pattern faded

Originally popularized by Dan Abramov: "smart" containers fetch data and manage state; "dumb" presentational components just render.

**Why it faded:** Hooks made it trivial to co-locate data-fetching logic *inside* a component without making the component "smart" in a way that hurts reusability. A `useUserData()` hook is more composable than a container HOC.

The pattern isn't wrong — it's just no longer the primary tool. You'll still see it implicitly (a page-level component fetches, passes to display components), but it's not enforced structurally.

### Compound components pattern

Allows a parent to share implicit state with children without prop drilling:

```tsx
interface TabsContextValue {
  activeTab: string;
  setActiveTab: (id: string) => void;
}

const TabsContext = React.createContext<TabsContextValue | null>(null);

function Tabs({ children, defaultTab }: { children: React.ReactNode; defaultTab: string }) {
  const [activeTab, setActiveTab] = React.useState(defaultTab);
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className="tabs">{children}</div>
    </TabsContext.Provider>
  );
}

function Tab({ id, children }: { id: string; children: React.ReactNode }) {
  const ctx = React.useContext(TabsContext);
  if (!ctx) throw new Error('Tab must be used inside Tabs');
  return (
    <button
      aria-selected={ctx.activeTab === id}
      onClick={() => ctx.setActiveTab(id)}
    >
      {children}
    </button>
  );
}

Tabs.Tab = Tab; // namespace on parent

// Usage:
<Tabs defaultTab="a">
  <Tabs.Tab id="a">First</Tabs.Tab>
  <Tabs.Tab id="b">Second</Tabs.Tab>
</Tabs>
```

**Trade-off:** Implicit coupling between parent and child. Children *must* be used inside the parent. This is intentional — it's the pattern's purpose.

---

## Props vs State

### Immutability of props and "lifting state up"

Props flow down. You never mutate them. If a child needs to signal a change, it calls a callback prop — state lives in the nearest common ancestor.

```tsx
function Parent() {
  const [value, setValue] = React.useState('');
  return <Child value={value} onChange={setValue} />;
}

function Child({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return <input value={value} onChange={e => onChange(e.target.value)} />;
}
```

### Derived state anti-pattern

```tsx
// Anti-pattern: copying props into state
function UserCard({ user }: { user: User }) {
  const [name, setName] = React.useState(user.name); // stale when user prop changes!
  // ...
}

// Correct: derive from props at render time
function UserCard({ user }: { user: User }) {
  const displayName = user.name.trim() || 'Anonymous'; // derived, always fresh
  // ...
}

// If you truly need to track a previous value, use a ref or key-reset pattern:
// <UserCard key={user.id} user={user} /> — reset all state when user changes
```

> ⚠️ Gotcha: `useState(props.x)` only uses the initial value on mount. If `props.x` changes later, state does NOT update. This is one of the most common senior-level bugs.

### Controlled vs uncontrolled inputs — the deep one

**Controlled:** React owns the value. The input is driven entirely by state.
```tsx
function ControlledInput() {
  const [value, setValue] = React.useState('');
  return <input value={value} onChange={e => setValue(e.target.value)} />;
}
```

**Uncontrolled:** The DOM owns the value. You read it via a ref when needed.
```tsx
function UncontrolledInput() {
  const ref = React.useRef<HTMLInputElement>(null);
  const handleSubmit = () => console.log(ref.current?.value);
  return <input ref={ref} defaultValue="" />;
}
```

**Trade-offs:**

| | Controlled | Uncontrolled |
|---|---|---|
| Validation on every keystroke | Yes | Requires manual listener |
| Format/mask as user types | Straightforward | Complex |
| Instant read at submit | Re-render on every key | Ref read — zero re-renders |
| File inputs | Impossible (read-only) | Required |
| Integration with 3rd-party DOM libs | Conflicts | Compatible |

> 💡 Senior insight: Libraries like React Hook Form default to *uncontrolled* inputs precisely because it eliminates per-keystroke re-renders. At scale, this is a significant performance win on large forms. Controlled inputs are correct for instant validation feedback, dependent fields, and formatted inputs like phone numbers or currency.

### Prop drilling and the ladder of solutions

```
1. Lift state up — fine for 1-2 levels
2. Component composition (children/slots) — often underused; pass JSX not just data
3. React Context — shared ambient data (theme, auth, locale)
4. Zustand / Jotai / Redux — cross-cutting state with complex update logic
5. URL / query params — state that should survive refresh or be shareable
```

**Composition is underused as a solution:**
```tsx
// Drilling: Parent → Middle → Child needs user
// Alternative: Parent composes, Middle doesn't know about user at all
function Page({ user }: { user: User }) {
  return <Layout sidebar={<UserCard user={user} />} />;
}
function Layout({ sidebar }: { sidebar: React.ReactNode }) {
  return <aside>{sidebar}</aside>; // no knowledge of user
}
```

---

## Events

### Synthetic events and React 17+ delegation change

React wraps native events in a `SyntheticEvent` for cross-browser normalization. Before React 17, all events were delegated to `document`. **Since React 17, they delegate to the root DOM container** (`ReactDOM.render` target).

**Why the change mattered:** Multiple React roots on the same page, or embedding React inside non-React apps, no longer have event interference. Stoppping propagation in one root doesn't silently swallow events in another.

### Event pooling — historical gotcha, now gone

Before React 17, `SyntheticEvent` objects were pooled and reused. Accessing `event.target` in an async callback would return null because the event was already recycled. The fix was `event.persist()`. React 17 removed pooling — events are now plain objects and the gotcha is gone, but you'll see it in legacy codebases and old Stack Overflow answers.

### Passing args to handlers

```tsx
// Anti-pattern: creates a new function every render (minor perf concern, but mostly style)
<button onClick={() => handleDelete(item.id)}>Delete</button>

// If identity matters (e.g. memoized child), use useCallback:
const handleDelete = React.useCallback((id: string) => {
  setItems(prev => prev.filter(i => i.id !== id));
}, []);

// Pass as data attribute (avoids closure, useful in lists):
<button data-id={item.id} onClick={handleDelete}>Delete</button>
function handleDelete(e: React.MouseEvent<HTMLButtonElement>) {
  const id = e.currentTarget.dataset.id;
}
```

### preventDefault and stopPropagation

```tsx
function Form() {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();     // stops browser default (page reload on form submit)
    e.stopPropagation();    // stops event bubbling to parent handlers
    // e.nativeEvent.stopImmediatePropagation() — stops OTHER listeners on the same element
  };
  return <form onSubmit={handleSubmit}>...</form>;
}
```

> ⚠️ Gotcha: `stopPropagation` only stops React's synthetic bubbling. Native event listeners attached directly to the DOM (outside React) can still fire because React's delegation fires first at the root.

---

## Lifecycle: Class to Hooks Mental Model

### Mapping class lifecycle methods to hooks

```tsx
// Class                          | Hook equivalent
// ─────────────────────────────────────────────────
// constructor / initial state    | useState(initialValue)
// componentDidMount              | useEffect(() => { ... }, [])
// componentDidUpdate(prev, snap) | useEffect(() => { ... }, [deps])
// componentWillUnmount           | useEffect(() => { return () => cleanup() }, [])
// shouldComponentUpdate          | React.memo + useMemo + useCallback
// getSnapshotBeforeUpdate        | useLayoutEffect (rare)
// componentDidCatch              | Error Boundary (class only, no hook equivalent yet)
```

### Effects are NOT lifecycle methods — senior critical point

`useEffect` is for **synchronizing with external systems**, not for reacting to lifecycle events. This mental shift matters:

```tsx
// Wrong mental model: "run this when count changes"
useEffect(() => {
  document.title = `Count: ${count}`;
}, [count]);
// Accidentally correct, but thinking about it this way leads to bugs.

// Correct mental model: "keep document.title synchronized with count"
// The effect runs whenever the synchronization needs to happen.
```

**The real consequence:** If you think in lifecycle terms, you write effects that fire "after mount" to fetch data. If you think in synchronization terms, you write effects that keep a data resource synchronized with an ID — and handle the case where that ID changes mid-life cleanly.

> 💡 Senior insight: Most "useEffect hell" comes from lifecycle thinking. The question to ask is not "when should this run?" but "what external system is this keeping in sync, and what is its dependency on React state?"

See **file 04 — Hooks** for deep useEffect coverage.

---

## Refs and the DOM

### When to use refs

Refs are imperative escape hatches. Use them when you need to:
- Manage focus, text selection, or media playback
- Trigger imperative animations
- Integrate with third-party DOM libraries
- Store mutable values that should not trigger re-renders

```tsx
function SearchInput() {
  const inputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    inputRef.current?.focus(); // imperative focus on mount
  }, []);

  return <input ref={inputRef} type="search" />;
}
```

### forwardRef — exposing a ref from a child

```tsx
const FancyInput = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  function FancyInput(props, ref) {
    return <input ref={ref} className="fancy" {...props} />;
  }
);

// React 19: ref is now a plain prop — forwardRef is no longer needed:
function FancyInput({ ref, ...props }: React.InputHTMLAttributes<HTMLInputElement> & { ref?: React.Ref<HTMLInputElement> }) {
  return <input ref={ref} className="fancy" {...props} />;
}
```

> ⚠️ Gotcha: Refs are not reactive. Reading `ref.current` in render is undefined behavior — the ref is populated after the DOM commits, and changing `ref.current` does not trigger a re-render.

**Follow-ups they'll ask:**
- When would you use `useImperativeHandle`?
- Difference between `useRef` and `createRef`?
- Why shouldn't you read `ref.current` during render?

---

## Error Boundaries

### What they catch — and what they don't

Error boundaries catch errors during **rendering**, **lifecycle methods**, and **constructors** of the subtree below them.

**They do NOT catch:**
- Errors in event handlers (use try/catch there)
- Async errors (`setTimeout`, `fetch`, promises)
- Errors in the error boundary itself
- Server-side rendering errors

```tsx
// Error boundaries must still be class components (no hook equivalent in React 18):
class ErrorBoundary extends React.Component<
  { fallback: React.ReactNode; children: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('Boundary caught:', error, info.componentStack);
  }

  render() {
    return this.state.hasError ? this.props.fallback : this.props.children;
  }
}
```

**Use `react-error-boundary` in production** — it provides `ErrorBoundary`, `useErrorBoundary()` hook, and `withErrorBoundary` HOC, handling reset and async error reporting cleanly.

```tsx
import { ErrorBoundary } from 'react-error-boundary';

<ErrorBoundary
  fallbackRender={({ error, resetErrorBoundary }) => (
    <div role="alert">
      <p>Something went wrong: {error.message}</p>
      <button onClick={resetErrorBoundary}>Try again</button>
    </div>
  )}
  onError={(error, info) => logToSentry(error, info)}
>
  <FeatureComponent />
</ErrorBoundary>
```

> 💡 Senior insight: Place error boundaries strategically — too high and an error in a widget crashes the whole page; too low and you have boilerplate everywhere. A good default: one at the app root (last resort), one per major page section, and one per independently fetchable feature.

---

## Portals

Portals render children into a DOM node outside the component's DOM hierarchy, while preserving React's tree (context, events still work normally).

```tsx
import { createPortal } from 'react-dom';

function Modal({ children, isOpen }: { children: React.ReactNode; isOpen: boolean }) {
  if (!isOpen) return null;
  return createPortal(
    <div className="modal-overlay" role="dialog" aria-modal="true">
      {children}
    </div>,
    document.getElementById('modal-root')!
  );
}
```

**Primary use case:** Modals, tooltips, dropdowns that need to escape `overflow: hidden` or `z-index` stacking contexts.

> ⚠️ Gotcha: Events bubble through the React tree, not the DOM tree. A click inside a portal bubbles to the portal's React parent, even though in the DOM it's a sibling of the root. This can cause unexpected event handler fires.

---

## Forms: Controlled vs Uncontrolled Trade-offs

### When uncontrolled + refs is actually better

For large forms with many fields where you only need the values on submit, uncontrolled inputs eliminate dozens of re-renders:

```tsx
function RegistrationForm() {
  const nameRef = React.useRef<HTMLInputElement>(null);
  const emailRef = React.useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
      name: nameRef.current!.value,
      email: emailRef.current!.value,
    };
    submitData(data);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input ref={nameRef} name="name" defaultValue="" />
      <input ref={emailRef} name="email" type="email" defaultValue="" />
      <button type="submit">Register</button>
    </form>
  );
}
```

### React 19 form actions (brief)

React 19 introduces `action` prop on `<form>` and the `useActionState` hook for server-integrated form handling without `onSubmit` boilerplate. See **file 08 — React 19 and Server Components** for full coverage.

---

## Conditional Rendering Pitfalls

```tsx
// Falsy pitfall: 0 renders as "0"
const items: string[] = [];
return <div>{items.length && <List items={items} />}</div>; // renders "0"!

// Fix options:
return <div>{items.length > 0 && <List items={items} />}</div>;
return <div>{items.length ? <List items={items} /> : null}</div>;

// undefined and null are safe — they render nothing:
return <div>{condition ? <Component /> : null}</div>; // always safe

// Boolean is safe too:
const show = false;
return <div>{show && <Component />}</div>; // renders nothing (boolean, not 0)
```

**Readability guideline:** Use ternary for two-branch conditions, `&&` only when the false branch is definitively `null`/nothing, and extract complex conditions into variables or early returns.

---

## StrictMode

### Double-invocation in development and why

```tsx
// main.tsx
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

In development, StrictMode deliberately:
1. Renders components twice (to surface impure render functions)
2. Runs effects twice — mounts, unmounts, then mounts again (to surface effects that don't clean up correctly)
3. Warns on deprecated API usage

**This is intentional.** If your component behaves differently on the second render, it has side effects during render — a bug. If your effect causes errors when run twice, its cleanup is broken.

```tsx
// Effect that breaks under StrictMode double-invoke — reveals missing cleanup:
useEffect(() => {
  const id = setInterval(tick, 1000);
  // missing: return () => clearInterval(id);
  // StrictMode: two intervals run, reveals the leak
}, []);

// Correct:
useEffect(() => {
  const id = setInterval(tick, 1000);
  return () => clearInterval(id);
}, []);
```

> 💡 Senior insight: StrictMode behavior in development does not occur in production. If your app "works in prod but not dev," StrictMode is exposing a real bug, not causing a false positive. Fix the bug.

> ⚠️ Gotcha: Third-party libraries that aren't StrictMode-compatible (fire-and-forget subscriptions, non-idempotent DOM mutations) will appear broken in development. The fix is either to find a cleaner integration or accept the library as a known non-strict dependency.

---

## ⚡ Rapid-Fire

- **What is the virtual DOM?** A JavaScript representation of the DOM that React diffs between renders to minimize real DOM mutations.
- **Is setState synchronous?** No — state updates are batched and applied asynchronously. React 18 batches all updates (including those in timeouts/promises) by default.
- **What is reconciliation?** The algorithm React uses to diff the previous and current virtual DOM trees and produce minimal DOM updates. Key prop is the primary identity hint.
- **Can you use hooks in class components?** No. Hooks are exclusively for function components.
- **What does `key` do when it changes?** React unmounts the old component and mounts a new one — all state is destroyed.
- **What is the difference between `defaultProps` and default parameter values?** `defaultProps` is a class/function static property (deprecated for function components in React 19). Default parameters in the function signature are idiomatic modern React.
- **When does a component re-render?** When its own state changes, when its parent re-renders (unless memoized), or when a consumed context value changes.
- **What is a pure component?** A component that returns the same output for the same props and has no side effects during render. `React.memo` is the function component equivalent of `PureComponent`.
- **What does `React.memo` do?** Wraps a component to skip re-rendering if props are shallowly equal to the previous render. It's an optimization, not a guarantee.
- **Can event handlers access stale state?** Yes — closures in event handlers capture the state from the render they were created in. Use the functional update form `setState(prev => ...)` to avoid this.
- **What is a controlled component?** A form element whose value is entirely driven by React state.
- **What is `useLayoutEffect`?** Like `useEffect` but fires synchronously after DOM mutations, before the browser paints. Use for measuring DOM layout.

---

## 🚩 Red Flags

- **Mutating state directly:** `this.state.items.push(x)` or `items.push(x); setItems(items)` — React won't detect the change.
- **Deriving state from props with useState:** `useState(props.value)` — stale after the prop changes.
- **Using array index as key on reorderable/filterable lists** — causes state mismatches and subtle rendering bugs.
- **Missing cleanup in useEffect** — subscriptions, intervals, and event listeners that aren't cleaned up cause memory leaks and StrictMode errors.
- **Reading ref.current during render** — undefined behavior; refs are populated post-commit.
- **Calling hooks conditionally** — `if (condition) { useState(...) }` violates the rules of hooks and will crash.
- **Ignoring the `0 &&` falsy render** — "why is there a zero on my screen?" is a classic junior mistake at a senior candidate's code review.
- **Confusing `stopPropagation` with `preventDefault`** — they do completely different things and conflating them reveals shallow understanding.
- **Assuming useEffect is "run on mount"** — it's synchronization, not lifecycle. Describing it as "runs on mount" in an interview is a yellow flag.
- **No error boundaries** — shipping a production app with no error boundary means one crashing widget takes down the entire page.
- **Over-engineering with Context** — reaching for Context for all shared state instead of first considering component composition or co-location.
- **Forgetting StrictMode double-invocation** — blaming React for "running my effect twice" when it's working as designed.
