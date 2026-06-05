# JavaScript Core: Senior Interview Deep Dive

The JS runtime model, closure semantics, and async coordination are the invisible substrate every React abstraction sits on. Interviewers probe these because stale closures, memory leaks, and microtask ordering bugs surface constantly in production React apps — and senior engineers are expected to debug them cold, not Google them.

---

## Execution Model

### Q: Walk me through what happens when this runs. What logs, and in what order?

```js
console.log('1');

setTimeout(() => console.log('2'), 0);

Promise.resolve().then(() => console.log('3'));

queueMicrotask(() => console.log('4'));

console.log('5');
```

**Answer:** `1 → 5 → 3 → 4 → 2`

The call stack runs synchronous code first: `1`, then `5`. When the stack empties, the event loop drains the **microtask queue** completely before pulling from the macrotask queue. `Promise.then` and `queueMicrotask` both schedule microtasks; they run in insertion order: `3`, then `4`. The `setTimeout` callback is a macrotask and runs last: `2`.

Mental model:

```
[Sync code] → [Drain all microtasks] → [One macrotask] → [Drain all microtasks] → repeat
```

> 💡 Senior insight: "0ms setTimeout" is not instant — it means "earliest next macrotask slot," which is always after all pending microtasks. This trips up junior engineers who use `setTimeout(fn, 0)` thinking it runs right after the current synchronous block, not realizing Promises queued before it will fire first.

**Trickier puzzle:**

```js
Promise.resolve()
  .then(() => {
    console.log('A');
    return Promise.resolve('B');
  })
  .then(v => console.log(v));

Promise.resolve().then(() => console.log('C'));
```

Output: `A → C → B`

`return Promise.resolve('B')` wraps the value in a *new* Promise internally resolved via two microtask ticks (one to resolve, one to then-schedule), so `C` from the independently-queued `.then` fires before `B`.

> 💡 Senior insight: Returning a *thenable* from a `.then` callback incurs an extra microtask turn. This is spec-compliant but surprises people who expect `Promise.resolve(value)` and `return value` to behave identically in chaining.

**Follow-ups they'll ask:**
- What is a macrotask vs microtask? Give concrete examples of each.
- Where does `requestAnimationFrame` fit in this model?
- How does the browser render/paint frame interact with the event loop?

---

### Q: When does the browser get a chance to render?

**Answer:** The render/paint step happens between macrotask executions — but only if the browser decides a visual update is needed. It never interrupts a running task or microtask drain. This means:

- A long synchronous task (>16ms) blocks the frame → jank.
- Flooding the microtask queue with recursive `Promise` chains also blocks rendering.
- `requestAnimationFrame` runs at the start of the *next* frame, before layout/paint, and is coordinated with the display refresh rate (typically 60Hz).

```js
// This will lock the UI — microtask flood
function flood() {
  Promise.resolve().then(flood); // never yields to macrotask queue
}
```

> 💡 Senior insight: React's concurrent scheduler uses `MessageChannel` (a macrotask) to yield back to the browser between render chunks — not Promises — specifically so the browser gets paint opportunities between React's work slices.

---

## Closures

### Q: What is a closure, and where does it cause bugs in React?

**Answer:** A closure is a function that captures its **lexical environment** — the variables in scope at the point of definition, not at call time. Every function in JS is a closure.

**Classic loop bug:**

```js
// Bug: all callbacks close over the same `i` binding (var is function-scoped)
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0); // logs 3, 3, 3
}

// Fix 1: let (block-scoped, new binding per iteration)
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0); // 0, 1, 2
}

// Fix 2: IIFE to capture value
for (var i = 0; i < 3; i++) {
  ((j) => setTimeout(() => console.log(j), 0))(i);
}

// Fix 3: bind or explicit closure param
for (var i = 0; i < 3; i++) {
  setTimeout(console.log.bind(null, i), 0);
}
```

**Stale closure in React:**

```tsx
// Bug: count is captured at render time the effect ran
useEffect(() => {
  const id = setInterval(() => {
    setCount(count + 1); // always reads the initial count
  }, 1000);
  return () => clearInterval(id);
}, []); // empty deps → stale closure

// Fix 1: functional updater (doesn't need the current value from closure)
setCount(prev => prev + 1);

// Fix 2: include count in deps (but recreates interval every second)
useEffect(() => {
  const id = setInterval(() => setCount(count + 1), 1000);
  return () => clearInterval(id);
}, [count]);

// Fix 3: useRef to hold latest value
const countRef = useRef(count);
useEffect(() => { countRef.current = count; }, [count]);
```

> 💡 Senior insight: The `eslint-plugin-react-hooks` exhaustive-deps rule exists entirely to catch stale closures. When you suppress it with `// eslint-disable-next-line`, you need to consciously justify why — usually it's because you've chosen the functional updater or ref pattern.

**Memory implications:** Closures keep their entire scope chain alive. If a closure captures a large array or DOM node, that memory cannot be GC'd until the closure itself is released. In React this manifests as leaked component state held by abandoned effect timers.

**Follow-ups they'll ask:**
- How does `useCallback` relate to closures?
- What's the difference between a stale closure and a stale ref?
- Can you explain how `useEvent` (or the `use` RFC pattern) addresses stale closures?

---

## `this` Binding

### Q: Explain the four `this` binding rules and where each applies.

**Answer:**

| Rule | How triggered | `this` is... |
|---|---|---|
| Default | Plain function call `fn()` | `undefined` (strict) / `globalThis` (sloppy) |
| Implicit | Method call `obj.fn()` | `obj` |
| Explicit | `.call(ctx)`, `.apply(ctx)`, `.bind(ctx)` | `ctx` |
| `new` | Constructor `new Fn()` | newly created object |

Arrow functions do **not** have their own `this` — they inherit from the enclosing lexical scope at definition time. There is no binding rule that can override it (`.call`, `.bind` are ignored for `this`).

**Losing `this` in callbacks:**

```js
class Timer {
  constructor() { this.ticks = 0; }

  start() {
    // Bug: regular function callback — this is undefined in strict mode
    setInterval(function () { this.ticks++; }, 1000);

    // Fix 1: arrow function (lexical this)
    setInterval(() => { this.ticks++; }, 1000);

    // Fix 2: explicit bind
    setInterval(function () { this.ticks++; }.bind(this), 1000);
  }
}
```

**In React class components (now mostly legacy):**

```jsx
// Bug: onClick handler loses this
<button onClick={this.handleClick}>  // handleClick called without obj context

// Fix: bind in constructor, or class field arrow function
handleClick = () => { this.setState(...) }; // arrow class field — lexical this
```

> 💡 Senior insight: Arrow class fields create a new function instance per instance (not shared on the prototype), which is a minor memory cost — a real trade-off in a list rendering 10k rows. The `bind in constructor` approach shares the prototype method but adds constructor verbosity. Know both, choose deliberately.

**Follow-ups they'll ask:**
- What does `new.target` do?
- Can you change `this` inside an arrow function with `.call`? (No — `this` is ignored.)
- How does `this` work in a React functional component? (It doesn't — hooks replaced it.)

---

## Prototypes & Inheritance

### Q: How does the prototype chain work, and what does `class` actually compile to?

**Answer:** Every JS object has an internal `[[Prototype]]` link. Property lookups walk this chain until the property is found or `null` is reached. `class` syntax is syntactic sugar over this mechanism — there is no separate "class system."

```js
class Animal {
  constructor(name) { this.name = name; }
  speak() { return `${this.name} makes a noise.`; }
}

class Dog extends Animal {
  speak() { return `${this.name} barks.`; }
}

// Equivalent prototype setup:
function Animal(name) { this.name = name; }
Animal.prototype.speak = function() { return `${this.name} makes a noise.`; };

function Dog(name) { Animal.call(this, name); }
Object.setPrototypeOf(Dog.prototype, Animal.prototype);
Dog.prototype.speak = function() { return `${this.name} barks.`; };
```

`Object.create(proto)` creates a new object with `proto` as its `[[Prototype]]` — useful for prototypal delegation without constructors.

```js
const base = { greet() { return `Hi, ${this.name}`; } };
const obj = Object.create(base);
obj.name = 'Vikash';
obj.greet(); // 'Hi, Vikash'
```

**Why it matters in React interviews:** Understanding that React components are just objects/functions with lifecycle hooks demystifies why `React.Component` works. More practically: knowing that `instanceof` checks traverse the prototype chain helps debug unexpected `false` results across iframes or module boundaries (different `Array` constructors).

> 💡 Senior insight: `class` fields with `#` (private) are not prototype-based — they use a `WeakMap` internally in the spec. They're truly private (not just convention), which changes the trade-off for data encapsulation vs reflection/testing needs.

**Follow-ups they'll ask:**
- What's the difference between `Object.create(null)` and `{}`?
- How would you implement mixin patterns without class inheritance?

---

## Async: Coordination Patterns

### Q: What are the practical differences between `Promise.all`, `allSettled`, `race`, and `any`?

```ts
const urls = ['https://api.example.com/a', 'https://api.example.com/b'];

// all: resolves when ALL resolve; rejects on first rejection (short-circuits)
const [a, b] = await Promise.all(urls.map(fetch)); // if b fails, a's result is lost

// allSettled: always resolves, gives {status, value/reason} for each
const results = await Promise.allSettled(urls.map(fetch));
const data = results.filter(r => r.status === 'fulfilled').map(r => r.value);

// race: resolves/rejects with whichever settles first
const fastest = await Promise.race([fetchA(), timeout(5000)]);

// any: resolves with first fulfillment; rejects (AggregateError) only if ALL reject
const firstSuccess = await Promise.any(mirrors.map(fetch));
```

> 💡 Senior insight: `Promise.all` fails silently on partial success — you get no data from any fulfilled promises when one rejects. `allSettled` is almost always the right choice for UI data fetching where you want to show partial results. Senior engineers reach for `allSettled` by default and justify departing from it.

**Sequential vs parallel — the common perf bug:**

```ts
// Bug: sequential — each await blocks the next (total time = sum of all)
const user = await fetchUser(id);
const posts = await fetchPosts(id);
const comments = await fetchComments(id);

// Fix: parallel — kick off all requests simultaneously (total time = slowest)
const [user, posts, comments] = await Promise.all([
  fetchUser(id),
  fetchPosts(id),
  fetchComments(id),
]);
```

**Error handling with async/await:**

```ts
// Pattern 1: try/catch (verbose but familiar)
try {
  const data = await fetchData();
} catch (err) {
  if (err instanceof NetworkError) { ... }
}

// Pattern 2: Go-style tuple (avoids nested try/catch in complex flows)
const [err, data] = await fetchData().then(d => [null, d]).catch(e => [e, null]);
```

**Async iteration (for await...of):**

```ts
async function* streamChunks(response: Response) {
  const reader = response.body!.getReader();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    yield value;
  }
}

for await (const chunk of streamChunks(response)) {
  // process each chunk as it arrives — real streaming
}
```

> 💡 Senior insight: This pattern is how you'd implement real-time AI text streaming in a React app — the generator yields chunks, and you update state incrementally rather than waiting for the full response.

**Follow-ups they'll ask:**
- How do you cancel a Promise / async operation?
- What is the difference between `async function` returning a value vs `return Promise.resolve(value)`?
- How does `AbortController` integrate with fetch and async flows?

---

## Coercion & Equality

### Q: When would you use `==`, `===`, and `Object.is`?

**Answer:** In modern codebases: almost always `===`. The rare legitimate use of `==` is `null == undefined` (true for both, checking "nullish" without importing a library). Every other `==` usage triggers type coercion that is almost never intentional.

```js
// Falsy values (8 of them)
false, 0, -0, 0n, '', null, undefined, NaN

// Surprising == coercions
0 == ''       // true — both coerce to 0
null == false // false — null only == undefined
[] == false   // true — [] → '' → 0, false → 0
[] == ![]     // true — ![] is false → 0; [] → 0
```

**`Object.is` vs `===`:**

```js
// Two cases where === lies:
NaN === NaN   // false — Object.is(NaN, NaN) → true
+0 === -0     // true  — Object.is(+0, -0)   → false
```

React's reconciler uses `Object.is` for shallow equality in `useMemo`, `useCallback`, and `React.memo` dependency comparisons. This means `-0` and `+0` are treated as different values — a real (if obscure) gotcha.

⚠️ **Gotcha:** `NaN !== NaN` breaks naive equality checks. Use `Number.isNaN(x)` (not the global `isNaN` which coerces first).

**Follow-ups they'll ask:**
- What are the falsy values in JS? (Memorize all 8.)
- Why is `typeof null === 'object'` a historical bug?

---

## Value vs Reference & Immutability

### Q: Why does React require new object references for state updates, and how do you efficiently produce them?

**Answer:** Primitives (`string`, `number`, `boolean`, `null`, `undefined`, `bigint`, `symbol`) are compared by value. Objects and arrays are compared by **reference** — two different objects with identical contents are `!==`. React's rendering bailout checks (via `Object.is`) see the same reference → no update needed.

```ts
// Bug: mutating state directly — same reference, React skips re-render
const [items, setItems] = useState([1, 2, 3]);
items.push(4);
setItems(items); // same array reference → no re-render

// Fix: produce new reference
setItems([...items, 4]);
setItems(prev => [...prev, 4]);
```

**Shallow vs deep copy:**

```ts
const shallow = { ...original };          // top-level copy, nested refs shared
const deep = structuredClone(original);   // ES2022 native deep clone, handles Date/Map/Set/circular refs

// structuredClone limitations: does NOT clone functions, DOM nodes, or class instances with methods
```

**Immutability patterns:**

```ts
// Object update (nested)
const updated = {
  ...state,
  user: {
    ...state.user,
    address: { ...state.user.address, city: 'Austin' },
  },
};

// Immer for complex nested updates (library-level, used by Redux Toolkit)
import produce from 'immer';
const next = produce(state, draft => {
  draft.user.address.city = 'Austin'; // looks like mutation, isn't
});
```

> 💡 Senior insight: Structural sharing (Immer's approach) is O(log n) for path-touched nodes, not O(n) full copy. This matters for large state trees. For flat state, spread is fine. Choosing the right pattern based on state shape is a senior judgment call.

**Follow-ups they'll ask:**
- What does `Object.freeze` do? Does it deep-freeze?
- How does `useImmer` compare to `useState` for complex nested state?

---

## Modules: ESM vs CommonJS

### Q: What are the practical differences between ESM and CJS, and why does it matter for bundle optimization?

**Answer:**

| | ESM | CommonJS |
|---|---|---|
| Syntax | `import`/`export` | `require`/`module.exports` |
| Loading | Static (parsed at compile time) | Dynamic (executed at runtime) |
| Tree-shaking | Yes — bundlers can eliminate unused exports | No — `require` is a function call |
| `this` at top level | `undefined` | `module.exports` |
| Top-level `await` | Yes (in module context) | No |
| Circular deps | Live bindings (TDZ safe) | Cached partial exports (bugs) |

**Tree-shaking depends on static analysis:**

```js
// Shakeable — bundler knows exactly what's imported at parse time
import { debounce } from 'lodash-es';

// Not shakeable — requires entire lodash
const _ = require('lodash');
const debounce = _.debounce;

// Also not shakeable — dynamic import at module level defeats static analysis
const util = await import(condition ? './a' : './b');
```

**Dynamic import for code splitting:**

```tsx
// React lazy loading — the canonical use of dynamic import()
const HeavyChart = React.lazy(() => import('./HeavyChart'));

// Conditional loading
if (user.isAdmin) {
  const { AdminPanel } = await import('./AdminPanel');
}
```

**Top-level await (ESM only):**

```ts
// Valid in .mjs or type: "module" package
const config = await fetch('/api/config').then(r => r.json());
export default config;
// Warning: blocks the entire module graph until resolved
```

> 💡 Senior insight: CJS `require` is synchronous, so it can't use top-level await. This is why Node's transition to ESM is painful — interop requires adapters or dual packages. In React-land, your bundler (Webpack/Vite/Rollup) handles this, but knowing the underlying reason explains why some packages publish both `main` (CJS) and `module` (ESM) fields in `package.json`.

---

## `let`/`const`/`var`, TDZ, Hoisting

### Q: Explain hoisting and the Temporal Dead Zone.

**Answer:** `var` declarations are hoisted to function scope and initialized to `undefined`. `function` declarations are hoisted and fully initialized. `let`/`const` are hoisted to block scope but are **not initialized** — accessing them before their declaration throws `ReferenceError`. The period between hoist and initialization is the Temporal Dead Zone (TDZ).

```js
console.log(x); // undefined (var hoisted + initialized)
var x = 5;

console.log(y); // ReferenceError: Cannot access 'y' before initialization (TDZ)
let y = 5;

// Function declaration — fully hoisted
greet(); // 'hello' — works
function greet() { return 'hello'; }

// Function expression — only the var is hoisted
greet2(); // TypeError: greet2 is not a function
var greet2 = function() { return 'hello'; };
```

⚠️ **Gotcha:** `class` declarations are also in the TDZ — you cannot use a class before its declaration, unlike function declarations.

> 💡 Senior insight: The TDZ exists specifically to prevent the confusing `var` behavior (accessing before assignment giving `undefined`). It makes `let`/`const` fail loudly rather than silently. This is why the rule "prefer `const` > `let` > avoid `var`" exists — predictable scoping and initialization.

---

## Iterators, Generators, Map/Set/WeakMap/WeakRef

### Q: When would you reach for a Generator over an async function, and what are the practical uses of WeakMap?

**Generators:**

```ts
function* range(start: number, end: number, step = 1) {
  for (let i = start; i < end; i += step) yield i;
}

// Lazy — only computes values on demand
for (const n of range(0, 1_000_000)) {
  if (n > 5) break; // only 6 iterations run
}

// Infinite sequences
function* fibonacci() {
  let [a, b] = [0, 1];
  while (true) {
    yield a;
    [a, b] = [b, a + b];
  }
}
```

**Generator use cases:** pagination streams, undo/redo stacks, state machines, Redux-Saga (which is built entirely on generators for testable async flows).

**Map vs Object:**

```ts
const map = new Map<object, string>(); // any value as key, including objects
map.set(domNode, 'metadata');         // Object keys are always strings/Symbols
map.size;                              // O(1) size
```

**Set for deduplication:**

```ts
const unique = [...new Set(arrayWithDups)];
```

**WeakMap — the senior answer:**

```ts
// WeakMap: keys must be objects; entries don't prevent GC of the key
const cache = new WeakMap<object, ComputedResult>();

function getComputed(obj: object) {
  if (!cache.has(obj)) cache.set(obj, compute(obj));
  return cache.get(obj)!;
}
// When obj is GC'd, its cache entry is automatically removed — no memory leak
```

> 💡 Senior insight: `WeakMap` is the right tool for associating metadata with DOM nodes or component instances without preventing their garbage collection. This is how React DevTools hooks into component instances internally, and how some memoization libraries avoid leaks.

**WeakRef** (ES2021): holds a weak reference to an object. Call `.deref()` to get it — returns `undefined` if GC'd. Useful with `FinalizationRegistry` for cleanup callbacks. Rarely needed in application code but good to know for library authoring.

---

## Debounce & Throttle

### Q: Implement debounce and throttle from scratch.

**Debounce** — delays execution until `delay`ms after the last call:

```ts
function debounce<T extends (...args: any[]) => any>(fn: T, delay: number) {
  let timer: ReturnType<typeof setTimeout> | null = null;

  const debounced = (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      fn(...args);
      timer = null;
    }, delay);
  };

  debounced.cancel = () => {
    if (timer) { clearTimeout(timer); timer = null; }
  };

  return debounced;
}

// Usage: search input — fire API call 300ms after user stops typing
const search = debounce((q: string) => fetchResults(q), 300);
```

**Throttle** — fires at most once per `interval`ms, then suppresses subsequent calls:

```ts
function throttle<T extends (...args: any[]) => any>(fn: T, interval: number) {
  let lastCall = 0;
  let timer: ReturnType<typeof setTimeout> | null = null;

  return (...args: Parameters<T>) => {
    const now = Date.now();
    const remaining = interval - (now - lastCall);

    if (remaining <= 0) {
      if (timer) { clearTimeout(timer); timer = null; }
      lastCall = now;
      fn(...args);
    } else {
      // Schedule trailing call so last invocation always fires
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => {
        lastCall = Date.now();
        timer = null;
        fn(...args);
      }, remaining);
    }
  };
}

// Usage: window scroll handler — fire at most once per 100ms
window.addEventListener('scroll', throttle(updatePosition, 100));
```

> 💡 Senior insight: The trailing-call logic in throttle is what distinguishes a production implementation from a naive one. Without it, rapid calls that end mid-interval leave the UI in a stale state. Lodash's `throttle` supports `{leading, trailing}` options — knowing why both exist shows you understand the real-world failure mode.

⚠️ **Gotcha:** In React, debounced/throttled functions must be stabilized with `useRef` or `useCallback` — recreating them on every render resets the timer.

```tsx
const debouncedSearch = useRef(debounce((q: string) => fetchResults(q), 300));
// or
const debouncedSearch = useMemo(() => debounce(fetchResults, 300), []);
```

**Follow-ups they'll ask:**
- What's the difference in UX between debounce and throttle for a scroll handler?
- How would you debounce an async function and cancel the previous request?
- How do you handle the React re-render case where the debounced function needs fresh state?

---

## Memory Leaks in JS/React

### Q: Describe five memory leak patterns in React and how to fix each.

**1. Detached DOM nodes held by closures:**

```js
// Bug: button is removed from DOM but held by the event listener closure
const button = document.querySelector('#btn');
button.addEventListener('click', () => expensiveOperation(button));
button.remove(); // detached, but button can't be GC'd — listener holds it
```

**2. setInterval/setTimeout not cleared:**

```tsx
useEffect(() => {
  const id = setInterval(poll, 5000);
  return () => clearInterval(id); // must return cleanup
}, []);
```

**3. Event listeners not removed:**

```tsx
useEffect(() => {
  const handler = (e: KeyboardEvent) => { ... };
  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler); // same reference required
}, []);
// Bug: if handler is recreated inline each render, removeEventListener won't find it
```

**4. Stale closure holding large component state:**

```tsx
// Bug: the callback captures the entire initial render's closed-over scope
const handler = useCallback(() => {
  doSomethingWith(giantDataset); // giantDataset from closure, never released
}, []); // empty deps means closure is never updated but also never GC'd
```

**5. WeakMap vs Map for component metadata (library code):**

```ts
// Bug: using Map with component instance as key prevents GC
const metadata = new Map(); // holds strong reference to key
metadata.set(componentInstance, { ... }); // instance can't be GC'd

// Fix
const metadata = new WeakMap(); // key is weakly held
```

**Detecting leaks:** Chrome DevTools Memory tab → Heap snapshot before/after → look for "Detached HTMLElement" nodes. React DevTools Profiler highlights components that re-render unexpectedly (a symptom of live stale closures).

> 💡 Senior insight: In React, the most common production memory leak is an unmounted component that still holds a `setState` callback (e.g., inside an uncleared fetch abort or timer). The classic error "Can't perform a React state update on an unmounted component" is the symptom — the fix is proper effect cleanup and `AbortController` for fetch.

---

## Currying & Partial Application

### Q: What is the difference between currying and partial application, and when do you actually reach for them?

**Answer:**

- **Currying** transforms a function of `n` arguments into a chain of `n` unary functions: `f(a, b, c)` becomes `f(a)(b)(c)`. Each call returns a new function until all arguments are supplied, then the original function executes.
- **Partial application** fixes some arguments of a function up front, returning a new function that accepts the remaining arguments. It does not require one argument at a time.

```js
// Currying: one arg per call
const add = a => b => a + b;
const add5 = add(5);
add5(3); // 8

// Partial application: fix one or more args at once
function multiply(a, b, c) { return a * b * c; }
const double = multiply.bind(null, 2);    // fixes only 'a'
double(3, 4); // 24
const doubleThenTriple = multiply.bind(null, 2, 3); // fixes a and b
doubleThenTriple(4); // 24
```

**Why/when use them:**

- **Point-free / pipeline style** — compose small, configured functions without naming intermediate data:
  ```js
  const pipeline = [double, add5, String].reduce((f, g) => x => g(f(x)));
  pipeline(3); // '11'
  ```
- **Reusable configured functions** — build a family of functions from one generic one:
  ```js
  const validateWith = schema => data => schema.safeParse(data);
  const validateUser = validateWith(userSchema);
  const validatePost = validateWith(postSchema);
  ```
- **React event handler factories** — avoid inline arrow functions on every render:
  ```tsx
  // Without currying: creates a new fn reference per render per item
  items.map(item => <button onClick={() => handleSelect(item.id)}>...</button>)

  // With currying: handleSelect(id) returns a stable handler shape
  const handleSelect = (id: string) => (e: React.MouseEvent) => {
    e.stopPropagation();
    dispatch({ type: 'SELECT', id });
  };
  items.map(item => <button onClick={handleSelect(item.id)}>...</button>)
  // Pair with useCallback + useMemo for full stability if needed
  ```

**Generic variadic `curry` implementation:**

```js
function curry(fn) {
  const arity = fn.length; // number of declared params

  return function curried(...args) {
    if (args.length >= arity) {
      return fn(...args); // enough args — execute
    }
    // Not enough args — return a function collecting more
    return function (...moreArgs) {
      return curried(...args, ...moreArgs);
    };
  };
}

// Usage
const curriedAdd = curry((a, b, c) => a + b + c);
curriedAdd(1)(2)(3);   // 6
curriedAdd(1, 2)(3);   // 6  — variadic: can pass multiple per call
curriedAdd(1)(2, 3);   // 6
```

The implementation relies on `fn.length` (the declared parameter count). This breaks with rest params (`...args`) or default params — both set `fn.length` to zero or fewer. Libraries like Ramda and `lodash/fp` use a manually specified arity for this reason.

**Partial application with `Function.prototype.bind`:**

```js
function request(method, url, data) {
  return fetch(url, { method, body: JSON.stringify(data) });
}

const get  = request.bind(null, 'GET');
const post = request.bind(null, 'POST');

get('/api/users');
post('/api/users', { name: 'Vikash' });
```

`bind` is the native partial-application tool for the leftmost arguments. For right-side or non-contiguous argument binding, you need a helper.

⚠️ **Gotcha:** Currying and point-free style can damage readability when overused. A chain of five curried functions with single-letter names is harder to debug than a straightforward named function. Reach for it when the abstraction genuinely reduces duplication — not to signal cleverness. TypeScript inference also degrades with deep curried signatures unless you annotate carefully.

**Follow-ups they'll ask:**
- What does `fn.length` return and what breaks it?
- How would you implement `partial` to allow gaps / placeholder arguments (like Ramda's `__`)?
- How is currying used in functional libraries like Ramda or `lodash/fp`?
- How do you keep a curried event handler stable across React re-renders?

---

## Polyfills

### Q: What is a polyfill, how does it differ from a transpile and a shim, and how do you write one correctly?

**Answer:**

| Term | What it does | Example |
|---|---|---|
| **Polyfill** | Implements a missing *runtime* API in JS, at runtime | `Array.prototype.flat` for IE11 |
| **Transpile** | Converts newer *syntax* to older syntax at build time | Arrow functions → `function` expressions via Babel |
| **Shim** | Broader term — any compatibility layer; polyfills are a subset. A shim may wrap an existing (broken) implementation, not just fill a missing one | `es5-shim` fixing `Array.prototype.forEach` in old IE |

A transpiler cannot add new runtime APIs (`Promise`, `fetch`, `ResizeObserver`) — those require polyfills. Both are needed together for full compatibility.

**How `core-js` + `babel-preset-env` + `browserslist` work together:**

```json
// .browserslistrc
> 0.5%
last 2 versions
not dead
```

```js
// babel.config.js
module.exports = {
  presets: [
    ['@babel/preset-env', {
      useBuiltIns: 'usage',  // inject only polyfills actually used in your code
      corejs: 3,             // pull from core-js v3
      targets: { browsers: ['> 0.5%', 'last 2 versions'] },
    }],
  ],
};
```

`useBuiltIns: 'usage'` statically analyzes your code, detects which APIs you call, cross-references the browserslist target support matrix, and injects only the necessary `core-js` imports. This is how you avoid shipping 40 KB of polyfills for a feature your codebase never uses. See **file 19 (build tools)** for the full Webpack/Vite integration details.

**Feature detection before patching prototypes:**

Always guard a polyfill with a feature check — never blindly overwrite a native implementation:

```js
if (!Array.prototype.flat) {
  Array.prototype.flat = function myFlat(depth = 1) { ... };
}
```

**Writing polyfills from scratch (classic interview asks):**

`Array.prototype.myMap`:

```js
if (!Array.prototype.myMap) {
  Array.prototype.myMap = function myMap(callback, thisArg) {
    if (typeof callback !== 'function') {
      throw new TypeError(callback + ' is not a function');
    }
    const result = new Array(this.length);
    for (let i = 0; i < this.length; i++) {
      if (i in this) { // skip holes in sparse arrays
        result[i] = callback.call(thisArg, this[i], i, this);
      }
    }
    return result;
  };
}
```

`Promise.all` polyfill:

```js
if (!Promise.all) {
  Promise.all = function promiseAll(iterable) {
    return new Promise((resolve, reject) => {
      const promises = Array.from(iterable);
      if (promises.length === 0) return resolve([]);

      const results = new Array(promises.length);
      let remaining = promises.length;

      promises.forEach((p, i) => {
        Promise.resolve(p).then(value => {
          results[i] = value;
          if (--remaining === 0) resolve(results);
        }, reject); // first rejection short-circuits
      });
    });
  };
}
```

`Function.prototype.bind` polyfill (frequently asked):

```js
if (!Function.prototype.bind) {
  Function.prototype.bind = function bind(thisArg) {
    if (typeof this !== 'function') {
      throw new TypeError('bind called on non-function');
    }
    const originalFn = this;
    const boundArgs = Array.prototype.slice.call(arguments, 1); // args after thisArg

    function Bound() {
      const callArgs = boundArgs.concat(Array.prototype.slice.call(arguments));
      // Support `new BoundFn()` — 'new' should ignore the bound 'this'
      return originalFn.apply(
        this instanceof Bound ? this : thisArg,
        callArgs
      );
    }

    // Preserve the prototype chain so instanceof checks work
    if (originalFn.prototype) {
      Bound.prototype = Object.create(originalFn.prototype);
    }
    return Bound;
  };
}
```

The `new` support (`this instanceof Bound`) is what separates a production polyfill from a naive one — when the bound function is used as a constructor, the bound `thisArg` must be ignored in favor of the newly created object.

**Risk of monkey-patching built-ins:**

Patching `Array.prototype` or `Object.prototype` pollutes the global scope for every piece of code in the runtime — including third-party libraries and browser extensions. The MooTools library famously patched `Array.prototype.flatten` with a different signature, which broke the TC39 proposal that later landed as `Array.prototype.flat`. Best practice: always guard with feature detection, never change existing method behavior, and prefer Symbol-keyed methods if you must add to built-ins in library code.

> 💡 Senior insight: In a modern React project, you rarely write polyfills by hand — `babel-preset-env` + `core-js` handles it automatically. But the interview asks about them because they test whether you understand the difference between build-time transformation and runtime API augmentation, know the prototype chain deeply enough to implement correctly, and are aware of the global-pollution risks that caused real ecosystem breakage. Understanding `Function.prototype.bind`'s `new` support also proves you've internalized how `new` works under the hood.

**Follow-ups they'll ask:**
- How would you polyfill `fetch`? (It's not on a prototype — it's a global. Add `window.fetch = ...` with the same feature check.)
- What is `useBuiltIns: 'entry'` vs `'usage'` in `babel-preset-env`?
- Why can't Babel transpile `Promise` without a polyfill?
- What went wrong with MooTools and `Array.prototype.flatten`?
- How would you test that your polyfill matches native behavior?

---

## ⚡ Rapid-Fire

**Q: Difference between `undefined` and `null`?**
A: `undefined` = variable declared but not assigned (or missing param/property). `null` = explicitly set to "no value." Both are falsy; `null == undefined` is true; `null === undefined` is false.

**Q: What does `typeof null` return?**
A: `'object'` — a historical bug in JS, unfixable for backward compat.

**Q: What is `NaN` and how do you check for it?**
A: Not-a-Number, result of invalid numeric ops. `typeof NaN === 'number'`. Check with `Number.isNaN(x)`, not `isNaN(x)` (which coerces first).

**Q: `const` means immutable?**
A: No — it means the binding can't be reassigned. The object the `const` points to is still mutable.

**Q: What triggers the TDZ error?**
A: Accessing a `let`/`const`/`class` variable before its declaration line is executed.

**Q: What does `structuredClone` not copy?**
A: Functions, DOM nodes, class methods (prototype chain), `Error` causes in some runtimes.

**Q: Microtask vs macrotask — give one example of each.**
A: Microtask: `Promise.then`, `queueMicrotask`, `MutationObserver`. Macrotask: `setTimeout`, `setInterval`, `MessageChannel`, I/O callbacks.

**Q: Can you `await` a non-Promise value?**
A: Yes — `await 42` wraps it in `Promise.resolve(42)`. It still yields one microtask tick.

**Q: What is `Promise.any` vs `Promise.race`?**
A: `race` resolves/rejects with first settled (including rejection). `any` resolves with first *fulfilled*, only rejects if all reject (`AggregateError`).

**Q: Why does `[] + []` equal `""`?**
A: Both coerce to `""` (via `.toString()`), string concatenation → `""`.

**Q: What is a Symbol used for?**
A: Unique, non-enumerable keys; well-known symbols (`Symbol.iterator`, `Symbol.toPrimitive`) hook into language protocols.

**Q: `for...in` vs `for...of`?**
A: `for...in` iterates *enumerable string keys* (including inherited). `for...of` iterates *values* of any iterable (array, Map, Set, generator). Never use `for...in` on arrays.

**Q: What does `Object.create(null)` give you?**
A: An object with no prototype — no `toString`, no `hasOwnProperty`. Used for pure hash maps to avoid prototype pollution attacks.

**Q: What is `void 0`?**
A: Evaluates expression, returns `undefined`. `void 0` is a reliable way to get `undefined` (before ES5, `undefined` was reassignable).

**Q: How does tree-shaking know what to remove?**
A: Static `import`/`export` analysis at bundle time. Side-effect-free marking in `package.json` (`"sideEffects": false`) tells bundlers they can safely drop unused exports.

**Q: What is the difference between currying and partial application?**
A: Currying converts a multi-argument function into a chain of unary functions (`f(a)(b)(c)`). Partial application fixes one or more arguments up front and returns a function awaiting the rest — it doesn't enforce one-arg-at-a-time.

**Q: What breaks the generic `curry(fn)` implementation based on `fn.length`?**
A: Rest parameters (`...args`) and default parameters — both cause `fn.length` to report 0 or fewer than expected, so the arity check never triggers and the function never executes.

**Q: Polyfill vs shim vs transpile — one-line each?**
A: Polyfill = JS code that implements a *missing* runtime API at runtime. Shim = any compatibility layer (may patch broken, not just absent, behavior). Transpile = build-time syntax conversion (arrow → function) — cannot add new APIs.

**Q: What is the difference between `call` and `apply`?**
A: Both invoke a function with explicit `this`. `call(ctx, arg1, arg2)` takes args spread; `apply(ctx, [arg1, arg2])` takes args as an array.

**Q: What does `new` do under the hood?**
A: Creates empty object, sets `[[Prototype]]` to constructor's `.prototype`, calls constructor with `this` = new object, returns that object (unless constructor returns a different object).

---

## 🚩 Red Flags

**Saying "`async/await` replaces Promises"** — async/await *is* Promises. Not understanding the substrate means you won't handle coordination patterns correctly.

**Using `var` "because it's equivalent to `let`"** — it's not. Function scope vs block scope, hoisting behavior, and TDZ are meaningfully different.

**`Promise.all` for all multi-fetch scenarios** — signals you haven't thought about partial failure. Interviewers notice when you don't mention `allSettled`.

**Empty `useEffect` deps with values used inside the effect** — screams stale closure problem. A senior should immediately reach for functional updater, ref, or correct deps.

**"Deep clone with `JSON.parse(JSON.stringify(obj))`"** — drops `undefined`, `Date`, `Function`, circular refs, `Map`/`Set`. A senior uses `structuredClone` or knows the limitations explicitly.

**"`===` and `Object.is` are the same"** — misses the `NaN`/`-0` edge cases that React's reconciler actually uses.

**Implementing debounce without a `cancel` method or trailing call** — the naive version breaks real use cases.

**Treating the event loop as FIFO without microtask/macrotask distinction** — will get the ordering puzzle wrong, which is a basic runtime knowledge check.

**"I use `console.log` to find memory leaks"** — should mention Heap snapshots, DevTools Memory panel, and detached node detection.

**"I avoid generators because they're confusing"** — fine in application code, but signals lack of familiarity with the iterator protocol that powers `for...of`, spread, destructuring, and async iteration.
