# React Senior/Lead Interview Cram Sheet

Use this the day before your interview. Every answer is the 30-second version designed for a 6-7 YOE senior/lead audience. Lead with the trade-off, not the definition. Deep-dives are linked to the numbered files in this kit — open them if an answer triggers a knowledge gap.

---

## JavaScript & TypeScript (→ files 01, 02)

**Q: Explain the event loop and microtask vs macrotask ordering.**

The call stack runs synchronously. When it empties, the engine drains the entire microtask queue (Promises, `queueMicrotask`, `MutationObserver`) before pulling the next macrotask (`setTimeout`, `setInterval`, I/O callbacks). The trade-off: microtasks can starve the rendering pipeline if you chain them infinitely — long `.then()` chains can delay a paint frame.

> 💡 `Promise.resolve().then(...)` fires before `setTimeout(fn, 0)` — always.

→ deep dive: file 01

---

**Q: Closures — explain and give a real use.**

A closure is a function that retains a reference to variables in its outer lexical scope after that scope has returned. The practical risk is inadvertent memory retention (closures holding large objects alive). A real use: a `createCounter()` factory that exposes `increment`/`reset` but hides the count variable — same pattern powers `useState` internally and every module that exposes a limited API surface.

→ deep dive: file 01

---

**Q: `==` vs `===` and type coercion.**

`===` checks value and type with no coercion — always prefer it. `==` applies the Abstract Equality Comparison algorithm: `null == undefined` is `true`, `"1" == 1` is `true`. The hidden danger is that coercion rules are non-obvious and differ across types; a linter rule (`eqeqeq`) just bans `==` outright in most teams.

→ deep dive: file 01

---

**Q: `this` binding rules.**

Four rules in priority order: `new` binding > explicit (`call`/`apply`/`bind`) > implicit (method call `obj.fn()`) > default (global/`undefined` in strict). Arrow functions capture `this` lexically at definition time, so they have no own `this` — critical distinction for React class methods vs arrow methods. The trade-off: arrow class fields are not on the prototype, so they don't benefit from inheritance.

→ deep dive: file 01

---

**Q: `Promise.all` vs `allSettled` vs `race`.**

`Promise.all` short-circuits on the first rejection — use when all results are required and a single failure should abort. `Promise.allSettled` waits for all and returns status+value/reason per promise — use when you want partial results and need to handle each failure independently. `Promise.race` resolves/rejects with the first settled promise — use for timeout patterns. Senior gotcha: `Promise.all` with an empty array resolves immediately.

→ deep dive: file 01

---

**Q: Debounce vs throttle.**

Both limit invocation frequency; the difference is the guarantee. Debounce fires only after the input has been silent for N ms — ideal for search-as-you-type (you care about the final value). Throttle fires at most once per N ms regardless of input frequency — ideal for scroll/resize handlers (you care about every Nth tick). The trade-off: debounce can feel laggy under continuous input; throttle can fire on a stale intermediate value.

> 💡 Debounce = "wait for silence." Throttle = "fire at a steady rate."

→ deep dive: file 01

---

**Q: Deep vs shallow clone.**

Shallow clone (`Object.assign`, spread `{...obj}`) copies top-level properties — nested objects are still shared references, so mutation propagates. Deep clone (structured clone via `structuredClone()`, or JSON round-trip) copies the full tree but is slower and `structuredClone` doesn't handle functions, `undefined`, or `Date` objects in all environments. JSON round-trip silently drops `undefined` and functions — a footgun in state management.

→ deep dive: file 01

---

**Q: `var` / `let` / `const` and TDZ.**

`var` is function-scoped and hoisted with value `undefined`. `let`/`const` are block-scoped and hoisted but not initialized — accessing them before declaration throws a `ReferenceError` (the Temporal Dead Zone). `const` prevents reassignment of the binding, not mutation of the value. Senior rule: prefer `const` by default, `let` when reassignment is needed, never `var`.

→ deep dive: file 01

---

**Q: `type` vs `interface` in TypeScript.**

Both describe object shapes, but the key differences: `interface` supports declaration merging (two `interface Foo` blocks merge), making it better for public library APIs that consumers extend. `type` supports union types, mapped types, and conditional types — making it more powerful for complex type algebra. In practice: use `interface` for object/class shapes, `type` for unions, intersections, and utility types.

> 💡 `type` can express `string | number`; `interface` cannot.

→ deep dive: file 02

---

**Q: Discriminated unions and exhaustiveness checking.**

A discriminated union shares a literal `kind`/`type` field across members so TypeScript narrows correctly in each `case`. Exhaustiveness is enforced by adding a `default` branch that assigns `never` to the discriminant — any unhandled case becomes a compile error. This is the right pattern for action types, API response variants, and state machines.

→ deep dive: file 02

---

**Q: `unknown` vs `any`.**

`any` disables type checking entirely — it infects callers. `unknown` is the type-safe top type: you can assign anything to it, but you cannot use it without a narrowing check (typeof, instanceof, type guard). Senior rule: ban `any` in CI via `@typescript-eslint/no-explicit-any`; use `unknown` at API boundaries where you genuinely don't control the shape.

→ deep dive: file 02

---

**Q: Generics in a component.**

Generics let a component be type-safe across different data shapes without duplicating code. Example: a `<List<T> items={T[]} renderItem={(item: T) => ReactNode} />` component. The trade-off: generic components are harder to read and can produce complex error messages; only add a generic when the type genuinely varies at the call site and you need type inference to flow through.

→ deep dive: file 02

---

## React Core (→ files 03, 04, 05)

**Q: What causes re-renders?**

Three triggers: state change (via `setState`/`useState` setter), parent re-render (by default, all children re-render), and context value change. The frequent senior mistake is blaming React for "too many re-renders" without measuring first — profiler often shows the root cause is an object literal or function created inline as a prop, producing a new reference every render.

→ deep dive: file 03

---

**Q: `React.memo` vs `useMemo` vs `useCallback`.**

`React.memo` is a component-level bailout — it skips re-rendering if props are shallowly equal. `useMemo` memoizes a computed value inside a component. `useCallback` memoizes a function reference. The trade-off: all three cost memory and add complexity; use them only when the Profiler confirms a performance problem — premature memoization is a real antipattern that adds maintenance burden with no measured gain.

> 💡 `useCallback(fn, deps)` is `useMemo(() => fn, deps)` — same mechanism, different ergonomics.

→ deep dive: file 04

---

**Q: `useEffect` vs `useLayoutEffect`.**

`useEffect` runs asynchronously after the browser has painted — correct for data fetching, subscriptions, analytics. `useLayoutEffect` runs synchronously after DOM mutations but before paint — use only when you need to read layout (scrollHeight, getBoundingClientRect) and apply a correction before the user sees it, to avoid flicker. The trade-off: `useLayoutEffect` blocks painting and will warn during SSR because the DOM doesn't exist on the server.

→ deep dive: file 03

---

**Q: Virtual DOM vs Real DOM — and the "it's faster" myth.**

The Virtual DOM is a lightweight in-memory representation of the UI tree. React diffs the previous and next VDOM and applies only the minimal set of real DOM mutations. The myth: VDOM is not categorically faster than direct DOM manipulation — a well-optimized vanilla update is faster than VDOM diffing. React's value is developer ergonomics and correctness guarantees, not raw DOM speed. Svelte compiles away the VDOM entirely.

→ deep dive: file 03

---

**Q: Explain React Fiber.**

Fiber is React's reconciliation engine (introduced in React 16). It represents each unit of work as a fiber node in a linked list, allowing React to pause, resume, abort, and prioritize work. This unlocks concurrent features: `startTransition` marks state updates as low priority so urgent updates (typing, clicking) can interrupt them. The trade-off: concurrent mode changes when effects and renders fire, which surfaced bugs in code that assumed synchronous render semantics.

→ deep dive: file 03

---

**Q: Why are keys important / index-as-key bug.**

Keys are React's hint for reconciliation — they tell React which list item maps to which fiber. Without stable keys, React destroys and recreates fibers on reorder, losing component state (input values, scroll position, animation state). Index-as-key is only safe when the list is static and never reordered or filtered. For dynamic lists, use a stable unique ID from the data.

→ deep dive: file 03

---

**Q: Controlled vs uncontrolled components.**

Controlled: React state is the source of truth; every keystroke calls a setter. Uncontrolled: the DOM is the source of truth; you read via `ref` on submit. The trade-off: controlled components give you instant validation and easy programmatic reset but re-render on every keystroke. Uncontrolled components are simpler and more performant for large forms but harder to validate in real-time. Libraries like React Hook Form use uncontrolled inputs under the hood for this reason.

→ deep dive: file 03

---

**Q: Stale closure problem.**

When a callback captures a state variable in a closure but the component re-renders with new state, the old callback still references the old value. Classic manifestation: a `setInterval` reading stale count. Solutions: use the functional updater form `setState(prev => prev + 1)`, or `useRef` to always hold the latest value. The root cause is that closures capture values, not bindings.

→ deep dive: file 04

---

**Q: Rules of hooks and why.**

Two rules: only call hooks at the top level (no conditionals/loops), and only call them from React functions. The "why" is the implementation: React tracks hooks by call order in a linked list per fiber — conditional calls break the index mapping between renders, causing state to be assigned to the wrong hook.

→ deep dive: file 04

---

**Q: `useRef` vs `useState`.**

`useState` triggers a re-render on change; `useRef` does not. Use `useRef` for: DOM node references, mutable values that should persist across renders without triggering paint (timers, previous values, third-party library instances). The senior mistake is using `useRef` for data that should drive the UI — the component will never re-render with updated values.

→ deep dive: file 04

---

**Q: Reconciliation in one paragraph.**

React calls `render()` (or the function component) to produce a new VDOM tree. Fiber diffs it against the current fiber tree using a heuristic O(n) algorithm: elements of different types are destroyed and recreated; elements of the same type are updated in place, preserving the fiber and its state. Keys identify list items across diffs. The result is a "work-in-progress" tree of effects (insertions, updates, deletions) that is committed to the real DOM in one synchronous flush.

→ deep dive: file 03

---

**Q: StrictMode double render.**

In development, StrictMode intentionally invokes render functions and state initializers twice to surface impure renders and side effects. Effects are also mounted, unmounted, and remounted. This is not a bug — it is a correctness probe. Production behavior is unaffected. The implication: any render-time side effect (console.log, network call, mutation) will appear twice in dev; that is the signal to move it into an effect.

→ deep dive: file 03

---

## State & Data (→ files 06, 15)

**Q: Context vs Redux.**

Context is a dependency-injection mechanism built into React — it is not a state management solution. Every context value change re-renders all consumers. Redux (via `react-redux` `useSelector`) gives fine-grained subscription: a component re-renders only when its selected slice changes. The trade-off: Redux is significant boilerplate for small apps; Context is fine for low-frequency global state (theme, locale, auth user) but fails for high-frequency updates like a real-time dashboard.

→ deep dive: file 06

---

**Q: Redux vs Zustand.**

Both are external stores. Redux enforces a strict unidirectional data flow with actions and reducers — good for teams that need auditability and DevTools time-travel. Zustand is a minimal store with direct mutation via Immer — far less boilerplate, easier to colocate, and just as testable. The trade-off: Zustand has fewer guardrails, which can lead to chaotic state mutation patterns on larger teams without discipline.

→ deep dive: file 06

---

**Q: Server state vs client state — why TanStack Query.**

Client state (selected tab, modal open, form input) lives in React state/Zustand. Server state (API responses) has fundamentally different properties: it is asynchronous, shared, can be stale, and needs caching/invalidation/refetching. TanStack Query treats server state as a cache problem rather than a state problem — it handles loading/error/stale states, background refetching, deduplication, and pagination with minimal code. Putting server data into Redux is an antipattern that recreates the same problems manually.

→ deep dive: file 06

---

**Q: When NOT to use Redux.**

When the app has no cross-cutting shared state, when the team size is 1-2 engineers, when all server state is handled by TanStack Query, or when the complexity of actions/reducers/selectors exceeds the complexity of the problem. A common architectural mistake is reaching for Redux in week one before the state requirements are understood — Zustand or Context is the right default until pain is felt.

→ deep dive: file 06

---

**Q: Optimistic updates.**

Apply the UI change immediately before the server confirms it, then roll back on error. TanStack Query's `onMutate` / `onError` / `onSettled` hooks implement this cleanly. The trade-off: optimistic UI feels instant but introduces reconciliation complexity — you must handle conflicts when the server response differs from the predicted state. Only worth it for high-latency, high-frequency user actions (likes, todos, drag-and-drop order).

→ deep dive: file 15

---

**Q: `staleTime` vs `gcTime` in TanStack Query.**

`staleTime` controls how long a cached response is considered fresh — during this window, no background refetch is triggered. `gcTime` (formerly `cacheTime`) controls how long unused cache entries are kept in memory before garbage collection. The trade-off: a long `staleTime` improves performance but risks showing outdated data; a short `gcTime` saves memory but causes more cache misses and loading states.

> 💡 `staleTime` = freshness window. `gcTime` = memory eviction window.

→ deep dive: file 15

---

**Q: WebSocket vs SSE vs polling.**

Polling is simple but wasteful — it fires requests regardless of new data. SSE (Server-Sent Events) is a unidirectional HTTP stream from server to client — ideal for notifications, live feeds, no client-to-server messaging needed. WebSocket is full-duplex — use when the client also sends real-time messages (chat, collaborative editing). The trade-off: WebSockets require a persistent connection and a stateful server; SSE rides HTTP/2 and is simpler to scale and proxy.

→ deep dive: file 15

---

**Q: How to prevent race conditions in data fetching.**

The classic bug: two sequential requests fire; the earlier one resolves last, overwriting the newer result. Solutions: (1) ignore stale responses by comparing a request ID or timestamp, (2) abort inflight requests via `AbortController` in a `useEffect` cleanup, (3) use TanStack Query which handles this internally. The `useEffect` cleanup pattern is the React-idiomatic answer for manual fetching.

→ deep dive: file 15

---

## Performance (→ files 07, 18)

**Q: How do you optimize a slow React app?**

Measure first — always. Open the React DevTools Profiler, record the slow interaction, identify the most expensive renders. Then: (1) eliminate unnecessary re-renders with `memo`/`useCallback` if confirmed, (2) lazy-load routes and heavy components, (3) virtualize long lists, (4) move expensive computation off the main thread if possible. Never guess and add `memo` everywhere — it has overhead and can mask the real problem.

→ deep dive: file 07

---

**Q: Why is a component re-rendering? (Diagnostic approach)**

Step 1: React DevTools Profiler → "highlight updates" → find the component. Step 2: check if a parent is re-rendering and the child is not memoized. Step 3: check if a prop is a new object/array/function reference created inline. Step 4: check if a context value is a new object reference. Step 5: check for state updates in effects that fire on every render. The majority of performance bugs are new reference identity issues, not computation.

→ deep dive: file 07

---

**Q: How do you analyze bundle size?**

Run `webpack-bundle-analyzer` or Vite's `rollup-plugin-visualizer` to get a treemap of the bundle. Look for: large libraries included entirely when only a sub-module is needed (lodash vs lodash-es), duplicate packages at different versions, large polyfills included unnecessarily. Then apply: dynamic `import()` for route-level code splitting, tree-shakeable imports, replacing heavy libraries with smaller alternatives. Target: no single vendor chunk over 200KB gzipped.

→ deep dive: file 07

---

**Q: Core Web Vitals and React causes.**

LCP (Largest Contentful Paint): caused by render-blocking resources, large images, SSR hydration delays — fix with preloading, image optimization, streaming SSR. INP (Interaction to Next Paint, replaced FID): caused by long tasks on the main thread from heavy synchronous renders — fix with `startTransition`, virtualization, debouncing. CLS (Cumulative Layout Shift): caused by images/iframes without dimensions, dynamically injected content — fix by reserving space with aspect-ratio CSS.

→ deep dive: files 07, 18

---

**Q: List virtualization — when and why.**

Render only the items currently visible in the viewport plus a small buffer. Use when a list exceeds ~100 items and DOM node count is causing jank or memory pressure. Libraries: `@tanstack/react-virtual` (headless), `react-window` (lightweight). The trade-off: virtualized lists break native browser find-in-page, accessibility tree enumeration, and can cause scroll anchor issues — only apply when profiling confirms it is needed.

→ deep dive: file 07

---

**Q: Reflow vs repaint.**

Repaint: visual property change (color, visibility) that does not affect layout — relatively cheap. Reflow (layout): geometry change (width, position, font-size) that forces the browser to recalculate element positions — expensive and cascades to descendants. Triggers to avoid: reading `offsetHeight`/`getBoundingClientRect` after a DOM write (forces synchronous layout), animating `width`/`height` instead of `transform`/`opacity`. Use DevTools Performance panel to find layout thrashing.

→ deep dive: file 18

---

**Q: Code splitting strategy.**

Route-level splitting with `React.lazy` + `Suspense` is the baseline — it is free and high-impact. Beyond that: split heavy third-party components (rich text editors, chart libraries) that are not needed on initial load. Use `prefetch` on likely-next routes. The trade-off: over-splitting creates many small requests and increases waterfall latency; HTTP/2 multiplexing mitigates this but there is still a per-request overhead.

→ deep dive: file 07

---

## Next.js & Rendering (→ file 08)

**Q: SSR vs CSR vs SSG vs ISR.**

CSR: browser fetches a blank HTML shell then loads everything via JS — worst LCP, best interactivity after load. SSR: server renders HTML per request — better LCP, but TTFB scales with server load. SSG: HTML generated at build time — best performance, but stale between deploys. ISR: SSG with background revalidation at a configured interval — the sweet spot for semi-dynamic content. The senior answer: choose based on data freshness requirements and server cost tolerance.

→ deep dive: file 08

---

**Q: RSC — server vs client components.**

Server Components (RSC) run only on the server: no event handlers, no hooks, no browser APIs, but can `async/await` data directly and contribute zero JS to the client bundle. Client Components (`"use client"`) run in the browser and support all React features. The key constraint: a Server Component cannot import a Client Component's state, but a Client Component can render Server Components as children via slots. RSC eliminates the fetch-then-hydrate waterfall for most data-fetching scenarios.

→ deep dive: file 08

---

**Q: The Next.js 14 → 15 caching change.**

In Next.js 14, `fetch` responses were cached by default (opaque background caching). Next.js 15 reversed this: `fetch` is uncached by default — you must explicitly opt in with `cache: 'force-cache'` or route-level `revalidate`. This was a correctness decision because silent caching caused data freshness bugs. The migration implication: any Next 14 app upgrading to 15 should audit every `fetch` call for unintended data staleness.

→ deep dive: file 08

---

**Q: Server Actions and security.**

Server Actions are async functions marked `"use server"` that execute on the server and can be called from Client Components like regular functions. Security concern: they are publicly callable HTTP endpoints — an attacker can POST to the action endpoint directly. Always validate input with a schema (Zod), authorize the request against the session, and never trust client-passed IDs for authorization. CSRF is mitigated by Next.js automatically for same-origin actions.

→ deep dive: file 08

---

**Q: When to choose Next.js over plain React.**

Choose Next.js when you need: SSR/SSG/ISR for SEO or LCP, a file-system router, built-in image/font optimization, API routes or Server Actions, or RSC. Stay with plain React (Vite/CRA) for: pure SPAs with no SEO requirements, Electron/desktop apps, library authoring, or teams that want full control over the build pipeline. The trade-off: Next.js adds framework opinions and version churn; you trade flexibility for features.

→ deep dive: file 08

---

## Architecture & System Design (→ files 12, 17)

**Q: Design a scalable dashboard.**

Key decisions: (1) server state via TanStack Query with per-widget cache keys and independent refetch intervals, (2) route-level code splitting per dashboard view, (3) widget-level error boundaries so one failure doesn't kill the page, (4) a design token system for consistent theming, (5) virtualize any data table over 100 rows. The trade-off: a highly componentized dashboard trades development speed for maintainability and testability.

→ deep dive: file 12

---

**Q: Design an infinite-scrolling feed.**

Use TanStack Query `useInfiniteQuery` for cursor-based pagination (not offset — offset breaks on inserts). Trigger fetch via `IntersectionObserver` on a sentinel element at the bottom. Virtualize with `@tanstack/react-virtual` once the list grows large. Handle loading/error/empty states per page. The trade-off: infinite scroll is an accessibility anti-pattern for keyboard users — provide a "load more" button as a fallback.

→ deep dive: file 12

---

**Q: Design a reusable component library.**

Decisions: (1) headless (Radix, Ariakit) for behavior + accessibility, custom styling on top, vs styled components. (2) design tokens as CSS custom properties for theming. (3) Storybook for documentation and visual regression. (4) versioned releases with a changelog — never break consumers silently. (5) peer-depend on React, don't bundle it. The trade-off: a custom component library has high upfront cost and ongoing maintenance — validate the need before building.

→ deep dive: file 17

---

**Q: Monolith vs micro-frontends.**

Micro-frontends split a large UI into independently deployable pieces (Module Federation, iframes, web components). Benefits: team autonomy, independent deploys, polyglot frameworks. Costs: shared state is painful, consistent UX requires discipline, performance degrades (duplicate React bundles unless carefully deduplicated), and operational complexity explodes. The honest senior answer: micro-frontends solve org problems, not engineering problems. Start with a monolith and extract only when Conway's Law forces it.

→ deep dive: file 17

---

**Q: Folder structure at scale.**

Feature-based structure scales better than type-based (`/components`, `/hooks`, `/utils` all mixed together). Group by domain: `features/auth/`, `features/dashboard/` with each containing its own components, hooks, and tests. Shared primitives go in `shared/ui/`. The rule of thumb: if two features need the same code, lift it to `shared/`; otherwise keep it colocated. The trade-off: feature boundaries require discipline — circular dependencies between feature folders are a code smell.

→ deep dive: file 17

---

**Q: Monorepo vs polyrepo.**

Monorepo (Nx, Turborepo): atomic commits across packages, easy code sharing, unified tooling, but requires sophisticated build caching and access control. Polyrepo: simple, independent CI, clear ownership, but cross-repo changes require coordination and shared code must be versioned and published. The inflection point: choose monorepo when two or more products share significant code and need to evolve together; choose polyrepo when teams are truly independent and sharing is rare.

→ deep dive: file 17

---

## Security & Accessibility (→ files 10, 11)

**Q: XSS and how React protects (and where it doesn't).**

React auto-escapes all JSX string values before inserting them into the DOM, preventing reflected/stored XSS via JSX. Where it does NOT protect: `dangerouslySetInnerHTML` (sanitize with DOMPurify before use), `href={userInput}` (a `javascript:` URL is not escaped — validate protocol), and `eval`/`new Function` with user input. Also: third-party scripts and browser extensions are outside React's scope.

→ deep dive: file 10

---

**Q: JWT in localStorage — why usually wrong.**

localStorage is accessible by any JavaScript on the page — a single XSS attack can exfiltrate the token and it cannot be revoked until expiry. The more secure alternative is `HttpOnly; Secure; SameSite=Strict` cookies, which are invisible to JavaScript. The trade-off: cookies require CSRF protection (SameSite mitigates this for modern browsers) and cannot be sent cross-origin without CORS configuration. For most apps, the cookie approach is the correct default.

→ deep dive: file 10

---

**Q: CSRF vs XSS.**

XSS: attacker injects and runs malicious script in your site's origin, with access to everything that origin can access. CSRF: attacker tricks an authenticated user's browser into making a request to your site from a different origin — the browser sends cookies automatically. The mitigations differ: XSS is prevented by output encoding and CSP; CSRF is prevented by `SameSite` cookies and/or CSRF tokens. They are not the same attack and do not share mitigations.

> 💡 XSS runs code in your origin. CSRF abuses your origin's cookies from elsewhere.

→ deep dive: file 10

---

**Q: Client route guards are not security.**

A React component that checks `if (!isAuthenticated) return <Navigate to="/login">` is a UX convenience, not a security control. The underlying API endpoints must enforce authorization independently because a determined user can bypass client-side checks by manipulating JS or calling the API directly. Never put sensitive data in a route that is only "protected" client-side.

→ deep dive: file 10

---

**Q: Semantic HTML vs ARIA.**

First rule of ARIA: don't use ARIA if a native HTML element provides the semantics. `<button>` is always better than `<div role="button">` because the native element includes keyboard focus, click-on-space/enter, and correct accessibility tree semantics for free. ARIA is for custom widgets with no HTML equivalent (combobox, tree, tab panel). Misused ARIA actively makes things worse — a `role="button"` on a `<div>` with no `tabIndex` is still not keyboard accessible.

→ deep dive: file 11

---

**Q: Keyboard accessibility essentials.**

All interactive elements must be reachable and operable via keyboard: focusable via Tab, activated via Enter/Space. Focus must never be trapped (except in modals, where it must be trapped and released on close). Focus must be visible — never `outline: none` without a replacement. Logical tab order follows DOM order — use `tabIndex="0"` only to add elements, never positive `tabIndex` values which create a confusing separate tab sequence.

→ deep dive: file 11

---

**Q: WCAG levels.**

Level A: minimum accessibility — missing this makes content inaccessible to some users. Level AA: the legal standard targeted by most regulations (ADA, EN 301 549, AODA) — this is what senior engineers must deliver. Level AAA: highest standard, not required for entire sites but worth targeting for critical flows. The practical implication: aim for AA compliance across all user-facing pages; AAA for core conversions like checkout or onboarding.

→ deep dive: file 11

---

## Testing & CI/CD (→ files 09, 20)

**Q: Testing pyramid vs trophy.**

The pyramid (unit > integration > e2e) was coined in a server-side context where unit tests were cheap and integration tests expensive. Kent C. Dodds' trophy inverts the ratio for frontend: most tests should be integration tests (component + real DOM + real interactions) because unit tests of a single function miss the glue code where most UI bugs live. E2e tests are the most confidence-giving but also the slowest and most flaky — write few, focused ones.

→ deep dive: file 09

---

**Q: Mock the network not modules (MSW).**

Mocking a module (jest.mock('../api/users')) couples tests to implementation details — refactoring the module path or library breaks tests for unrelated reasons. MSW (Mock Service Worker) intercepts at the network level via a service worker in the browser or Node intercepts in tests — your components make real `fetch`/`axios` calls and get realistic responses. The tests are now decoupled from implementation and test the real integration path.

→ deep dive: file 09

---

**Q: Jest vs Vitest.**

Both use the same assertion API (Jest-compatible). Vitest runs natively in the Vite ecosystem, supports ES modules without transformation, and is significantly faster for Vite projects due to shared config. Jest requires `babel-jest` or `ts-jest` for transformation and is slower in large projects. The migration path is low-friction for most codebases. The trade-off: Jest has a larger ecosystem of matchers and community plugins; Vitest is catching up rapidly.

→ deep dive: file 09

---

**Q: When is e2e worth it?**

E2e tests (Playwright, Cypress) are slow, flaky, and expensive to maintain — worth it for: critical user journeys (signup, checkout, login), smoke tests against production deployments, and multi-page flows that are impractical to test at a lower level. Not worth it for: every feature, UI polish, or error states that can be tested in integration tests. The rule: write e2e tests for paths where a failure is catastrophic and cannot be caught by a unit or integration test.

→ deep dive: file 09

---

**Q: What gates a PR in CI?**

A mature frontend CI pipeline gates on: type check (`tsc --noEmit`), lint (`eslint --max-warnings 0`), unit/integration tests with coverage threshold, bundle size budget check (fail if bundle grows by >X%), and accessibility checks (`axe-core` or `@axe-core/playwright`). Optionally: visual regression snapshots, Lighthouse CI score. The principle: nothing that passes CI should introduce a regression visible to users or reviewers.

→ deep dive: file 20

---

**Q: Feature flags — why.**

Feature flags decouple deployment from release: code ships to production hidden behind a flag, and activation is a configuration change not a deploy. This enables: trunk-based development (no long-lived feature branches), gradual rollouts (10% of users), instant rollback (flip the flag), and A/B testing. The trade-off: flags accumulate technical debt — every flag must have a removal plan and a cleanup ticket created at the time it is introduced.

→ deep dive: file 20

---

**Q: Blue-green vs canary.**

Blue-green: two identical environments; traffic switches atomically from old (blue) to new (green). Fast rollback by switching back. Requires double the infrastructure during transition. Canary: new version receives a small percentage of traffic alongside the old version; percentage grows as confidence increases. Canary catches real-world issues with limited blast radius but is more complex to orchestrate and monitor. For frontend, canary is typically implemented via feature flags or CDN traffic splitting.

→ deep dive: file 20

---

## Behavioral / Senior (→ file 13)

For all behavioral questions, the interviewer is assessing a specific dimension. The STAR skeleton (Situation, Task, Action, Result) is the frame — but lead with the Action and Result, not the backstory. Prepare 4-5 real stories and fit them to the question.

**Q: Hardest technical decision.**

Assessing: technical judgment, trade-off reasoning, comfort with ambiguity. STAR focus: what were the competing options, what data/principles drove the decision, what was the outcome and what would you do differently. → deep dive: file 13

---

**Q: Disagreement with a teammate.**

Assessing: collaboration, intellectual humility, ability to influence. STAR focus: how you listened first, what data or principle you used to make the case, and how you reached resolution (yours/theirs/compromise) without damaging the relationship. → deep dive: file 13

---

**Q: A production incident you owned.**

Assessing: ownership, composure under pressure, systematic debugging, post-mortem mindset. STAR focus: how you detected it, how you communicated, what the root cause was, what you changed to prevent recurrence. Demonstrating a blameless post-mortem mindset is the senior signal. → deep dive: file 13

---

**Q: How you mentor.**

Assessing: leadership, patience, whether you can scale your impact. STAR focus: a concrete example of guiding a junior through a problem (Socratic rather than telling), the outcome for them, and what you learned about teaching. → deep dive: file 13

---

**Q: Influencing without authority.**

Assessing: communication, strategic thinking, political navigation. STAR focus: a situation where you had no direct authority (cross-team, stakeholder, org change), how you built consensus using data and relationships, and the outcome. → deep dive: file 13

---

## The 20 You Must Not Fumble

The highest-frequency questions across all rounds. Know these cold.

| # | Question | One-line answer |
|---|----------|-----------------|
| 1 | What causes a React re-render? | State change, parent re-render, or context value change. |
| 2 | `useMemo` vs `useCallback` | One memoizes a value, the other a function reference — same mechanism. |
| 3 | Microtask vs macrotask order | Microtask queue drains fully before the next macrotask runs. |
| 4 | Stale closure fix | Use functional updater `setState(prev => ...)` or a ref for the latest value. |
| 5 | `unknown` vs `any` | `any` disables type checking; `unknown` requires a narrowing check before use. |
| 6 | RSC vs Client Component | RSC: zero client JS, async data, no hooks. Client: interactive, hooks, browser APIs. |
| 7 | Index-as-key bug | Causes React to destroy and recreate fibers on list reorder, losing local state. |
| 8 | Context re-render problem | Every consumer re-renders on any value change; use external store for high-frequency state. |
| 9 | `useEffect` cleanup | Return a function to abort fetches or unsubscribe — prevents memory leaks and race conditions. |
| 10 | TanStack Query vs Redux for server data | Server state is a caching problem, not a state problem — Query handles staleness, refetch, dedup. |
| 11 | WCAG AA | The legal-compliance target; A is minimum, AAA is aspirational. |
| 12 | XSS in React | Auto-escaped in JSX; `dangerouslySetInnerHTML` and `href` with `javascript:` are the gaps. |
| 13 | JWT in cookie vs localStorage | Cookie with `HttpOnly; SameSite=Strict` is invisible to JS; localStorage is XSS-vulnerable. |
| 14 | SSR vs SSG | SSR renders per request (fresh, slower); SSG renders at build time (fast, can be stale). |
| 15 | `useLayoutEffect` use case | Reading DOM layout before paint to prevent visual flicker — otherwise use `useEffect`. |
| 16 | Debounce vs throttle | Debounce fires after silence; throttle fires at a steady rate. |
| 17 | Code splitting baseline | `React.lazy` + `Suspense` at route boundaries — free and highest impact. |
| 18 | Testing trophy | More integration tests than unit tests for frontend; e2e for critical paths only. |
| 19 | Micro-frontends honest answer | They solve org/team autonomy problems, not engineering problems; default to monolith. |
| 20 | Feature flag benefit | Decouples deployment from release, enabling gradual rollout and instant rollback. |
