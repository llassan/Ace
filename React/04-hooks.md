# React Hooks — Deep Dive for Senior/Lead Interviews

Hooks are the mechanism by which React function components participate in the fiber reconciliation lifecycle — they are not syntactic sugar over class methods, they are a fundamentally different model. At the senior level, interviewers probe whether you understand the fiber-linked-list storage model, closure semantics, and the discipline required to avoid subtle bugs in concurrent mode.

---

## Rules of Hooks — The Mechanism Behind the Rule

### Why can't you call hooks conditionally or in loops?

**Mental model:** React stores hook state as a singly linked list on the fiber node. Each `useState`, `useEffect`, etc. appends a node to that list on the first render. On every subsequent render, React walks the list in order, matching the nth call to the nth node. If call order changes — because of a conditional or early return — node n is matched to the wrong state slot and the runtime explodes silently or throws.

```ts
// Fiber hook list (simplified conceptual model):
// fiber.memoizedState -> { state: 0, next -> { effect: fn, next -> null } }
//                        ^useState #1          ^useEffect #1
```

This is why the rule is enforced by `eslint-plugin-react-hooks`, not the runtime — the runtime will only throw at the mismatched hook, not the conditional.

> 💡 Senior insight: The linked-list model also explains why hooks cannot be called inside async functions, event handlers, or class components — those execution contexts never have a "current fiber" set by the React reconciler.

⚠️ Gotcha: React 19 introduces the `use()` hook which *can* be called conditionally. It is not stored in the fiber list the same way — it participates in Suspense and Promise unwrapping, not persistent state.

**Follow-ups they'll ask:**
- "What does `eslint-plugin-react-hooks` exhaustive-deps actually check?" (dependency arrays are statically analyzed for closure captures)
- "Could React have used a different storage mechanism?" (yes — key-based maps, but linked lists match call order with O(1) per hook)

---

## useState — Snapshots, Batching, and Lazy Initialization

### What is "state as a snapshot" and why does it matter?

**Mental model:** Each render captures a fixed snapshot of state. The `count` you close over in a render function is the value at that render's invocation — not a live reference. Calling the setter schedules a new render with a new snapshot.

```ts
const [count, setCount] = useState(0);

function handleClick() {
  setCount(count + 1); // count is 0 here
  setCount(count + 1); // count is STILL 0 here — same snapshot
  // result: count becomes 1, not 2
}

// Fix: functional update reads from reconciler's latest committed state
function handleClickFixed() {
  setCount(c => c + 1);
  setCount(c => c + 1); // result: count becomes 2
}
```

Functional updates are *required* when the new state depends on the previous value and multiple updates may be queued in the same synchronous batch.

### When is lazy initialization important?

```ts
// Expensive computation runs on EVERY render — wrong
const [data, setData] = useState(parseHeavyJSON(rawInput));

// Lazy init: the function is called only on mount
const [data, setData] = useState(() => parseHeavyJSON(rawInput));
```

The initializer function is invoked exactly once. This matters for any non-trivial computation, reading from `localStorage`, or constructing objects.

### How does React 18 automatic batching change things?

Before React 18, batching only occurred inside React event handlers. React 18 batches all updates regardless of origin — `setTimeout`, `Promise.then`, native event listeners.

```ts
// React 17: two separate renders
// React 18: one render (batched)
setTimeout(() => {
  setCount(c => c + 1);
  setName('Alice');
}, 1000);

// Opt out if you genuinely need intermediate renders
import { flushSync } from 'react-dom';
flushSync(() => setCount(c => c + 1));
flushSync(() => setName('Alice'));
```

> 💡 Senior insight: Automatic batching can expose bugs in code that relied on synchronous re-renders as a side-effect ordering mechanism. If you have `useEffect` that reads state you expected to be settled, audit call sites after upgrading.

**Follow-ups they'll ask:**
- "Difference between `setState(x)` and `setState(() => x)`?" (former is the value, latter receives pending state and is safer under batching)
- "Can state updates be synchronous?" (no — scheduling is always async, `flushSync` forces a synchronous flush of the queue)

---

## useEffect — Synchronization, Not Lifecycle

### What is the correct mental model for useEffect?

**Mental model:** Effects *synchronize* your component with an external system (DOM API, WebSocket, analytics, timers). They are not `componentDidMount` / `componentDidUpdate` / `componentWillUnmount` — thinking in lifecycle terms leads to over-firing and stale bugs.

The question to ask: "What external system does this effect keep in sync, and how do I clean up when it's no longer needed?"

```ts
useEffect(() => {
  const sub = store.subscribe(handler); // synchronize
  return () => sub.unsubscribe();       // desynchronize
}, [store, handler]);
```

### Explain the stale closure problem and its three fixes.

When an effect closes over state or props from a prior render snapshot, it reads stale values. This is the #1 source of subtle hook bugs.

```ts
// STALE: interval captures count=0 on mount, never updates
useEffect(() => {
  const id = setInterval(() => {
    setCount(count + 1); // always 0 + 1
  }, 1000);
  return () => clearInterval(id);
}, []); // empty deps — intentional but broken
```

**Fix 1: Functional update (preferred for state)**
```ts
setCount(c => c + 1); // no closure over count needed
```

**Fix 2: Ref for latest value (when you need to read without re-subscribing)**
```ts
const countRef = useRef(count);
useEffect(() => { countRef.current = count; }); // sync ref every render

useEffect(() => {
  const id = setInterval(() => {
    setCount(countRef.current + 1); // always fresh
  }, 1000);
  return () => clearInterval(id);
}, []); // safe because we read from ref
```

**Fix 3: useReducer (effect only needs dispatch, which is stable)**
```ts
const [state, dispatch] = useReducer(reducer, initial);

useEffect(() => {
  const id = setInterval(() => dispatch({ type: 'INCREMENT' }), 1000);
  return () => clearInterval(id);
}, []); // dispatch is referentially stable
```

### Why do objects/functions in the dependency array cause infinite loops?

Every render creates a *new* object/function reference even if the contents are identical. React compares deps with `Object.is` — two separately created `{}` objects fail the comparison, triggering the effect, which triggers a render, which creates a new object...

```ts
// Infinite loop: options is recreated each render
useEffect(() => {
  fetchData(options);
}, [options]); // new reference every render

// Fix: stabilize reference with useMemo, or extract primitive deps
const stableOptions = useMemo(() => ({ page, filter }), [page, filter]);
useEffect(() => {
  fetchData(stableOptions);
}, [stableOptions]);
```

### What is useEffectEvent and when will you use it?

`useEffectEvent` (React 19 stable, previously experimental as `useEvent`) extracts the "event" part of an effect — logic that should always see fresh values but should not be a dependency.

```ts
import { useEffect, useEffectEvent } from 'react';

function ChatRoom({ roomId, onMessage }: Props) {
  const handleMessage = useEffectEvent((msg: Message) => {
    // always sees latest onMessage — not a dep
    onMessage(msg);
  });

  useEffect(() => {
    const socket = connect(roomId);
    socket.on('message', handleMessage);
    return () => socket.disconnect();
  }, [roomId]); // onMessage correctly excluded
}
```

> 💡 Senior insight: `useEffectEvent` is the principled solution to the pattern of stuffing callbacks into refs. It makes the intent explicit and will be lint-enforced.

### How do you handle race conditions in data-fetching effects?

```ts
useEffect(() => {
  let cancelled = false;
  const controller = new AbortController();

  async function load() {
    try {
      const res = await fetch(`/api/user/${userId}`, {
        signal: controller.signal,
      });
      const data = await res.json();
      if (!cancelled) setUser(data); // guard against stale set
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') return;
      if (!cancelled) setError(e);
    }
  }

  load();
  return () => {
    cancelled = true;
    controller.abort();
  };
}, [userId]);
```

The `cancelled` flag guards `.json()` resolution; `AbortController` cancels the network request. Both are necessary because `abort()` only rejects the fetch, not subsequent awaits.

### When should you NOT use an effect?

- **Derived state:** compute it during render, not in an effect setting state.
- **Transforming data for rendering:** filter/sort/map in the render body or `useMemo`.
- **Responding to user events:** put logic in the event handler, not an effect that watches state.
- **Resetting state on prop change:** prefer the `key` prop to unmount/remount.
- **Communicating with a parent component:** call the callback in the event handler.

> 💡 Senior insight: An effect that sets state unconditionally will always cause a double render. If you find yourself writing `useEffect(() => { setState(derive(props)); }, [props])`, you have derived state — compute it inline.

**Follow-ups they'll ask:**
- "What is Strict Mode's double-invocation doing?" (it mounts, unmounts, remounts in dev to surface effects that don't clean up correctly)
- "Why does React run effects after paint, not before?" (to avoid blocking the browser; layout effects run before paint for DOM measurements)

---

## useLayoutEffect vs useEffect

### When is useLayoutEffect necessary?

**Mental model:** `useLayoutEffect` fires synchronously after DOM mutations but before the browser paints. It blocks paint, so use it only when you must read layout (getBoundingClientRect, scroll position) and synchronously write to avoid flicker.

```ts
useLayoutEffect(() => {
  // Read DOM, then adjust — no visible flash
  const { height } = ref.current.getBoundingClientRect();
  setTooltipPosition(calculatePosition(height));
}, []);
```

Use `useEffect` for everything else — subscriptions, analytics, non-visual side effects. A rough decision rule: if the user would see a flash without it, use `useLayoutEffect`.

⚠️ Gotcha: `useLayoutEffect` runs in the browser only. On the server it is a no-op with a warning. Use `useEffect` for SSR-compatible code or guard with `typeof window !== 'undefined'`.

---

## useRef — Mutable Box and DOM Access

### What are the two distinct use cases for useRef?

**Mental model 1 — Mutable box:** A ref is a plain object `{ current: T }` that persists across renders without triggering re-renders. Use it to store values that the rendering logic does not need to react to: interval IDs, previous values, "did mount" flags, latest callback references.

```ts
const latestCallback = useRef(onSave);
useEffect(() => { latestCallback.current = onSave; }); // sync without dep

// Interval reads fresh callback without becoming a dep
useEffect(() => {
  const id = setInterval(() => latestCallback.current(), 1000);
  return () => clearInterval(id);
}, []);
```

**Mental model 2 — DOM ref:** Pass to a JSX element's `ref` prop for imperative DOM access (focus, scroll, measurement).

```ts
const inputRef = useRef<HTMLInputElement>(null);
// After mount: inputRef.current is the DOM node
```

**Ref callbacks** fire with the node when attached and `null` when detached — useful for measuring or registering elements that mount conditionally.

```ts
const measureRef = useCallback((node: HTMLDivElement | null) => {
  if (node) setHeight(node.getBoundingClientRect().height);
}, []);
```

⚠️ Gotcha: Reading `ref.current` during render is legal but dangerous in concurrent mode — the ref may be mutated between render and commit. Only read refs in effects or event handlers.

---

## useReducer — When State Gets Complex

### When does useReducer outperform useState?

Use `useReducer` when:
1. Next state depends on previous state in complex ways.
2. Multiple sub-values are updated together (related state).
3. The update logic is complex enough to warrant testing in isolation.
4. You want to pass dispatch (stable) instead of multiple setters down the tree.

```ts
type State = { status: 'idle' | 'loading' | 'error'; data: User | null; error: string | null };
type Action =
  | { type: 'FETCH_START' }
  | { type: 'FETCH_SUCCESS'; payload: User }
  | { type: 'FETCH_ERROR'; payload: string };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'FETCH_START':  return { status: 'loading', data: null, error: null };
    case 'FETCH_SUCCESS': return { status: 'idle', data: action.payload, error: null };
    case 'FETCH_ERROR':  return { status: 'error', data: null, error: action.payload };
  }
}

const [state, dispatch] = useReducer(reducer, { status: 'idle', data: null, error: null });
```

> 💡 Senior insight: `dispatch` is referentially stable across renders (like `setState`). This makes it safe to include in dependency arrays or pass as a prop without wrapping in `useCallback`.

---

## useContext — Re-renders and the Identity Pitfall

### How does context cause unnecessary re-renders and how do you fix it?

Every component that calls `useContext(MyContext)` re-renders whenever the context *value* changes, determined by `Object.is`. If the provider renders a new object literal as its value, every consumer re-renders on every parent render.

```ts
// Bad: new object reference on every render
<AuthContext.Provider value={{ user, logout }}>

// Fix: memoize the value
const value = useMemo(() => ({ user, logout }), [user, logout]);
<AuthContext.Provider value={value}>
```

**Split contexts** by update frequency — separate rarely-changing values (theme) from frequently-changing values (current user session) so consumers only subscribe to what they need.

```ts
const ThemeContext = createContext<Theme>('light');
const UserContext = createContext<User | null>(null);
// Components reading theme don't re-render on user changes
```

`React.memo` on consumers only helps if the context value is also stable. If the context value is unstable, `memo` will not save you.

> 💡 Senior insight: Context is not a state management replacement. It shines for dependency injection (theme, locale, auth) and colocation with `useReducer`. For high-frequency updates, reach for Zustand/Jotai/useSyncExternalStore.

---

## useMemo / useCallback — When They Help and When They Hurt

### What is the actual guarantee these hooks provide?

`useMemo(() => compute(a, b), [a, b])` returns a memoized value — the function only re-runs when `a` or `b` changes. `useCallback(fn, deps)` is `useMemo(() => fn, deps)` — it returns a stable function reference.

They provide **referential stability** and optionally **computation caching**. Neither is free: they add memory overhead and the cost of comparing dependencies on every render.

```ts
// Legitimate: stabilize a callback passed to a memoized child
const handleSubmit = useCallback(
  (data: FormData) => submitMutation(data, userId),
  [submitMutation, userId]
);

// Legitimate: expensive derivation
const sortedItems = useMemo(
  () => items.slice().sort(compareFn),
  [items, compareFn]
);

// Pointless: primitive computation is cheaper than memo overhead
const doubled = useMemo(() => count * 2, [count]); // just write count * 2
```

**When they HURT:**
- Wrapping cheap computations adds cost without benefit.
- Incomplete dependency arrays create stale closures inside memoized functions.
- Over-memoizing encourages "dependency honesty" violations — you add a dep, memoization breaks, you remove the dep to stop re-renders, and now you have a stale bug.

> 💡 Senior insight: Profile before memoizing. The React DevTools Profiler highlights which components render and why. Memoize at the boundary of a known slow subtree, not preemptively across the codebase.

⚠️ Gotcha: React may discard memoized values (e.g., in concurrent mode under memory pressure). Never rely on `useMemo` for semantic correctness — only for performance.

**Follow-ups they'll ask:**
- "If `useCallback` wraps a function that uses a stale dep, what happens?" (the stale dep is captured at memoization time — this is the dependency honesty problem)

---

## useImperativeHandle — Rare but Legitimate

### When would you actually reach for useImperativeHandle?

When exposing an imperative API from a child component to a parent via ref, while keeping internal DOM nodes encapsulated. Classic use cases: custom input components, animation controllers, scroll utilities.

```ts
interface VideoPlayerHandle {
  play: () => void;
  seek: (time: number) => void;
}

const VideoPlayer = forwardRef<VideoPlayerHandle, Props>((props, ref) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  useImperativeHandle(ref, () => ({
    play: () => videoRef.current?.play(),
    seek: (t) => { if (videoRef.current) videoRef.current.currentTime = t; },
  }), []);

  return <video ref={videoRef} {...props} />;
});
```

> 💡 Senior insight: If you find yourself wanting this, first ask if the API can be modeled declaratively through props. `useImperativeHandle` is correct for focus management in complex custom inputs, not for replacing prop-driven state.

---

## useDebugValue — DevTools Labeling for Custom Hooks

### What does useDebugValue do and when should you use it?

**Mental model:** `useDebugValue` attaches a label to a custom hook that is displayed in the React DevTools "Hooks" panel. It has zero effect on behavior and zero effect in production — it exists purely to improve the developer experience when inspecting hook state.

Two critical constraints: it only works **inside custom hooks** (not components), and it **only affects DevTools display**.

```ts
function useOnlineStatus(): boolean {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handler = () => setIsOnline(navigator.onLine);
    window.addEventListener('online', handler);
    window.addEventListener('offline', handler);
    return () => {
      window.removeEventListener('online', handler);
      window.removeEventListener('offline', handler);
    };
  }, []);

  // DevTools shows: OnlineStatus: "Online" or "Offline"
  useDebugValue(isOnline ? 'Online' : 'Offline');

  return isOnline;
}
```

**Lazy-formatting second argument:** if computing the display value is expensive, pass a formatter function as the second argument. React only calls it when the hook is actually being inspected in DevTools, not on every render.

```ts
useDebugValue(connectionStats, (stats) =>
  `${stats.latency}ms — ${stats.packetLoss}% loss`
);
```

This deferred form is the right default any time the label requires non-trivial computation (date formatting, JSON serialization, string interpolation over large objects).

> 💡 Senior insight: `useDebugValue` is a library-author tool. If you are publishing a custom hook package, label internal state so consumers get a meaningful DevTools view instead of raw primitives. In application code, use it only on hooks complex enough that raw state values are ambiguous without context.

⚠️ Gotcha: `useDebugValue` is a no-op in production builds — React strips it. Never use it to drive logic, surface errors to users, or as a substitute for proper logging. Overusing it on simple hooks adds noise to the DevTools panel without benefit.

---

## Concurrent Mode Hooks — useDeferredValue, useTransition, useSyncExternalStore, useId

### What problem does useTransition solve?

Marks state updates as non-urgent. React can interrupt and deprioritize the transition update to keep the UI responsive. The `isPending` flag lets you show a loading indicator without blocking the current UI.

```ts
const [isPending, startTransition] = useTransition();

function handleSearch(q: string) {
  startTransition(() => setQuery(q)); // non-urgent
}
```

`useDeferredValue` is the consumer-side equivalent — defer a value you receive (e.g., a prop) rather than a value you set.

### Why does useSyncExternalStore exist?

In concurrent mode, React may render a component multiple times before committing. If an external store (Redux, Zustand, custom event emitter) mutates between these renders, different components may read different values — this is "tearing." `useSyncExternalStore` prevents tearing by subscribing synchronously and re-rendering when the store changes.

```ts
const count = useSyncExternalStore(
  store.subscribe,         // subscribe(onStoreChange): () => unsubscribe
  () => store.getCount(),  // getSnapshot (client)
  () => 0                  // getServerSnapshot (SSR)
);
```

> 💡 Senior insight: All modern state management libraries (Zustand, Redux Toolkit, Jotai) use `useSyncExternalStore` internally. You rarely call it directly unless building a library.

### What is useId for?

Generates a stable, unique ID that is consistent between server and client (solving SSR hydration mismatches for `htmlFor`/`id` pairs).

```ts
function FormField({ label }: { label: string }) {
  const id = useId();
  return (
    <>
      <label htmlFor={id}>{label}</label>
      <input id={id} />
    </>
  );
}
```

---

## React 19 Hooks — use(), useActionState, useFormStatus, useOptimistic

### What does the use() hook change?

`use()` unwraps a Promise or Context inside a render function and can be called conditionally (unlike other hooks). It integrates with Suspense — the component suspends until the Promise resolves.

```ts
import { use, Suspense } from 'react';

function UserCard({ userPromise }: { userPromise: Promise<User> }) {
  const user = use(userPromise); // suspends if pending
  return <div>{user.name}</div>;
}

// Parent wraps with Suspense
<Suspense fallback={<Skeleton />}>
  <UserCard userPromise={fetchUser(id)} />
</Suspense>
```

This replaces the common `useEffect` + `useState` data-fetching pattern for cases where the data source is a Promise passed as a prop.

### useActionState — what does it replace?

```ts
const [state, action, isPending] = useActionState(
  async (prevState: State, formData: FormData) => {
    const result = await submitForm(formData);
    return result;
  },
  initialState
);
```

Replaces the manual `useReducer` + `useTransition` + loading state pattern for form submissions and server actions. Works with React Server Components and form `action` props.

### useFormStatus and useOptimistic

`useFormStatus` reads the pending state of the nearest ancestor `<form>` — useful for submit button components that don't receive the pending flag as a prop.

```ts
function SubmitButton() {
  const { pending } = useFormStatus();
  return <button disabled={pending}>{pending ? 'Saving...' : 'Save'}</button>;
}
```

`useOptimistic` applies an optimistic update that is automatically rolled back or replaced when the async action settles.

```ts
const [optimisticLikes, addOptimisticLike] = useOptimistic(
  likes,
  (currentLikes, _) => currentLikes + 1
);
```

> 💡 Senior insight: React 19's form hooks reduce the boilerplate that previously drove developers to libraries like react-hook-form for basic cases. For complex multi-step forms with validation, libraries still win.

---

## Custom Hooks — Extraction, Composition, and Quality Patterns

### What makes a hook worth extracting?

Extract when: behavior is reused across components, OR the hook encapsulates a coherent concern that would clutter the component, OR you want to test the behavior in isolation.

Return **tuples** when there are exactly two values with a clear primary/secondary relationship (like `useState`). Return **objects** when there are more than two values or the names matter for clarity.

**useDebounce**
```ts
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
```

**useLocalStorage**
```ts
function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') return initialValue;
    try {
      const item = window.localStorage.getItem(key);
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      setStoredValue(prev => {
        const next = value instanceof Function ? value(prev) : value;
        try { window.localStorage.setItem(key, JSON.stringify(next)); } catch {}
        return next;
      });
    },
    [key]
  );

  return [storedValue, setValue] as const;
}
```

**useFetch with cancellation**
```ts
type FetchState<T> = { data: T | null; error: Error | null; loading: boolean };

function useFetch<T>(url: string): FetchState<T> {
  const [state, dispatch] = useReducer(
    (_: FetchState<T>, action: Partial<FetchState<T>>) => ({ ..._, ...action }),
    { data: null, error: null, loading: true }
  );

  useEffect(() => {
    const controller = new AbortController();
    dispatch({ loading: true, error: null });

    fetch(url, { signal: controller.signal })
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json() as Promise<T>; })
      .then(data => dispatch({ data, loading: false }))
      .catch(error => {
        if (error.name !== 'AbortError') dispatch({ error, loading: false });
      });

    return () => controller.abort();
  }, [url]);

  return state;
}
```

**Testing custom hooks:** Use `@testing-library/react`'s `renderHook`. Wrap state updates in `act`. Mock timers for debounce tests.

```ts
import { renderHook, act } from '@testing-library/react';

it('debounces value', async () => {
  vi.useFakeTimers();
  const { result, rerender } = renderHook(
    ({ val }) => useDebounce(val, 300),
    { initialProps: { val: 'a' } }
  );
  rerender({ val: 'b' });
  expect(result.current).toBe('a');
  act(() => vi.advanceTimersByTime(300));
  expect(result.current).toBe('b');
});
```

> 💡 Senior insight: A good custom hook name always starts with `use` and describes the *behavior*, not the implementation. `useDebounce` is better than `useTimeout`. `useSelectedUser` is better than `useContextUser`.

---

## ⚡ Rapid-Fire

- **What is the `exhaustive-deps` lint rule checking?** — That every variable captured in a `useEffect`/`useMemo`/`useCallback` callback is listed as a dependency.
- **Can you put an async function directly in `useEffect`?** — No. `useEffect` must return `undefined` or a cleanup function. Async functions return Promises. Define async inside the effect and call it.
- **What happens if you return a non-function from `useEffect`?** — React throws in development. Only `undefined` or a function is valid.
- **Why is `useLayoutEffect` called after mutations but "before paint"?** — It runs in the same synchronous flush as the DOM write, before the browser compositor has a chance to render the updated DOM.
- **What does `useId` guarantee that `Math.random()` in render does not?** — Hydration consistency — the server and client generate the same ID for the same component instance in the tree.
- **Is `dispatch` from `useReducer` stable across renders?** — Yes, guaranteed by React, same as the `setState` setter.
- **What is the "tearing" problem in concurrent mode?** — Multiple renders reading different snapshots of an external mutable store, resulting in UI inconsistency within a single committed render.
- **Can `useMemo` return a different value without dependencies changing?** — Yes, React may discard memoized values as an optimization. Never rely on memo for semantic guarantees.
- **Difference between `null` and `undefined` as a dependency?** — `Object.is(null, undefined)` is `false` — React treats them as different values and will re-run the effect on the transition.
- **What does `useOptimistic` do on error?** — Reverts to the actual state passed to it. The optimistic value is a UI overlay, not committed state.
- **What does `useDebugValue` do?** — Labels a custom hook in React DevTools; it is a no-op in production and must only be called inside custom hooks.

---

## 🚩 Red Flags

- Calling `setState` or `dispatch` inside a `useEffect` without a guard — signals derived state or missing dependency that causes an infinite loop.
- Empty dependency array `[]` with a closure over props or state — almost always a stale closure bug waiting to be filed.
- `useEffect` used exclusively as `componentDidMount` / `componentDidUpdate` — candidate doesn't understand the synchronization model.
- Objects or functions constructed inline as dependency array members — will cause the effect to re-run on every render.
- `useMemo` and `useCallback` on every function and value without profiling — cargo-cult memoization that adds overhead and dependency maintenance burden.
- Mutating `ref.current` during render — safe only in effects and event handlers; during render it conflicts with concurrent mode.
- Not cleaning up subscriptions, intervals, or WebSocket connections — resource leaks and Strict Mode double-invocation failures.
- Using context for high-frequency state (mouse position, scroll) without `useSyncExternalStore` — causes pervasive re-renders and potential tearing.
- `async` function directly passed to `useEffect` — returns a Promise instead of a cleanup function, suppresses cleanup, triggers lint errors.
- Ignoring the `useEffectEvent` / ref-latest-value pattern for callbacks — copy-pasted stale closure fixes that don't compose cleanly.
