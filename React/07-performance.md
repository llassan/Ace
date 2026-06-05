# React Performance

Performance optimization without measurement is superstition. Before touching a single `useMemo`, open React DevTools Profiler, establish a baseline flamegraph, and pinpoint the actual bottleneck — re-render frequency, expensive computation, network waterfall, or bundle weight. Most production slowness comes from one of four causes; cargo-cult memoization fixes none of them and adds maintenance debt to all of them.

---

## Measure-First Discipline

### Q: What's your process before writing any optimization code?

**Diagnosis before prescription.** The order matters: reproduce the symptom under realistic conditions, measure to find the hotspot, apply a targeted fix, re-measure to confirm improvement.

**Tool stack:**

| Tool | What it answers |
|------|----------------|
| React DevTools Profiler | Which components re-render, how often, how long each commit takes |
| Chrome Performance panel | Long tasks, main-thread blocking, scripting vs. rendering vs. painting breakdown |
| Lighthouse / PageSpeed Insights | Core Web Vitals score, opportunity flags, lab + field data |
| `why-did-you-render` | Logs *why* a component re-rendered (same-reference props, context changes) |
| React Scan | Visual overlay showing render frequency in real time; zero config |
| `performance.mark` / `performance.measure` | Custom timing for specific interactions in production |

**React DevTools Profiler workflow:**

1. Enable "Record why each component rendered" in DevTools settings.
2. Start recording, perform the slow interaction, stop.
3. Look at the flamegraph: tall bars = expensive renders, wide bars = many components in a commit.
4. Click a component — the sidebar shows the render reason (props changed, hooks changed, parent re-rendered).
5. Sort by "Render duration" to find the single most expensive component — fix that one first.

```tsx
// Instrument custom timing in production builds
function ExpensiveList({ items }: { items: Item[] }) {
  useEffect(() => {
    performance.mark("ExpensiveList-start");
    return () => {
      performance.mark("ExpensiveList-end");
      performance.measure("ExpensiveList", "ExpensiveList-start", "ExpensiveList-end");
    };
  });
  // ...
}
```

> 💡 Senior insight: React DevTools Profiler only runs in development mode. For production bottlenecks, use the User Timing API (`performance.mark`) combined with RUM (Real User Monitoring) tools like Datadog, Sentry Performance, or web-vitals library sending to your analytics backend.

⚠️ Gotcha: The Profiler shows *commit* time, not *render* time. A component can be expensive to render but cheap to commit (e.g., no DOM mutations). Focus on interactions that feel slow to the user, not just components with long render bars in isolation.

**Follow-ups they'll ask:**
- How do you profile in production without DevTools?
- What's the difference between a flame chart and a flame graph?
- How does `why-did-you-render` differ from DevTools Profiler?

---

## Core Web Vitals

### Q: What are Core Web Vitals and how does React affect them?

Google's field metrics for real-user experience. These gate SEO ranking and are the most honest signal of perceived performance.

**LCP — Largest Contentful Paint** (target: ≤ 2.5s)

Measures when the largest visible element (hero image, h1, video poster) finishes rendering.

*React causes:* Client-side rendering delays LCP because the browser must download JS, parse it, execute it, and then paint. A blank `<div id="root">` is not LCP content.

*Fixes:*
- SSR or SSG to ship HTML content immediately (see file 08).
- Preload the LCP image: `<link rel="preload" as="image" href="/hero.avif">`.
- Use `next/image` with `priority` prop on above-the-fold images.
- Avoid lazy-loading the LCP element.

**INP — Interaction to Next Paint** (target: ≤ 200ms)

Replaced FID (First Input Delay) in March 2024. FID only measured the *delay before* an event handler ran; INP measures the *full interaction latency* — from input event through to the browser painting the visual response. INP is a much stricter and more representative metric.

*React causes:* Heavy synchronous state updates blocking the main thread, large component trees re-rendering on every keystroke, long tasks during event handlers.

*Fixes:*
```tsx
// Bad: synchronous heavy update blocks paint
function SearchBar() {
  const [query, setQuery] = useState("");
  const results = expensiveFilter(data, query); // blocks every keystroke

  return <input onChange={e => setQuery(e.target.value)} />;
}

// Good: useTransition marks result update as non-urgent
function SearchBar() {
  const [query, setQuery] = useState("");
  const [deferredQuery, setDeferredQuery] = useState("");
  const [isPending, startTransition] = useTransition();

  const results = useMemo(() => expensiveFilter(data, deferredQuery), [deferredQuery]);

  return (
    <input
      onChange={e => {
        setQuery(e.target.value); // urgent: update input immediately
        startTransition(() => setDeferredQuery(e.target.value)); // non-urgent
      }}
      value={query}
    />
  );
}
```

**CLS — Cumulative Layout Shift** (target: ≤ 0.1)

Measures unexpected layout shifts. Score = impact fraction × distance fraction, summed.

*React causes:* Images without explicit dimensions, dynamic content injected above existing content, fonts causing FOUT, skeleton screens that differ in size from real content.

*Fixes:*
```tsx
// Always reserve space for async content
function Avatar({ src }: { src: string }) {
  return (
    <div style={{ width: 48, height: 48 }}> {/* explicit dimensions prevent shift */}
      <img src={src} width={48} height={48} alt="" />
    </div>
  );
}
```

**FCP — First Contentful Paint** (target: ≤ 1.8s): First pixel of text or image. Affected by render-blocking resources and TTFB.

**TTFB — Time to First Byte** (target: ≤ 800ms): Server response time. Not React's fault per se, but streaming SSR improves it by flushing the shell early.

> 💡 Senior insight: INP replacing FID in 2024 was a significant change because INP catches jank that FID missed — a page could have good FID but terrible INP if interactions after the first one are slow. React's `useTransition` and `useDeferredValue` are direct tools for improving INP scores.

⚠️ Gotcha: Lighthouse runs in a throttled lab environment. Your INP score in the field (Chrome UX Report / CrUX) often differs significantly. Always check both.

**Follow-ups they'll ask:**
- How would you debug a high INP score on a specific page?
- What's the difference between FID and INP?
- How does streaming SSR improve LCP?

---

## Re-Render Optimization

### Q: When does React.memo actually help, and when is it harmful?

`React.memo` prevents re-render when all props pass shallow equality. It helps when: the component is expensive to render AND its parent re-renders frequently AND its props are stable.

It is **useless** when:
- Props include objects/functions created inline (new reference every render).
- The component renders rarely anyway.
- The component is trivially cheap to render.

It is **harmful** when:
- You wrap every component by default (maintenance cost, false security).
- It masks the real problem (a parent that shouldn't re-render at all).

```tsx
// Useless: inline object creates new reference every render
const Parent = () => <Child config={{ theme: "dark" }} />; // memo won't help
const Child = memo(({ config }) => <div>{config.theme}</div>);

// Useful: stable reference + expensive render
const config = { theme: "dark" }; // defined outside component or memoized

const HeavyChart = memo(({ data, config }: Props) => {
  // expensive D3 calculations...
  return <canvas ref={canvasRef} />;
});
```

### Q: Honest guidance on useMemo and useCallback?

See file 04 for deep coverage. The honest summary:

- `useCallback` is only useful when the function is a prop to a `memo`-wrapped child or a dependency of another hook. Otherwise it adds overhead with zero benefit.
- `useMemo` is only useful when the computation is genuinely expensive (benchmark: >1ms) or when you need referential stability for a downstream memo/hook.
- Both have a cost: memory for the cached value, comparison on every render.

**React Compiler (React 19):** The compiler automatically inserts memoization equivalent to `useMemo`/`useCallback`/`memo` where it statically determines it's safe. For components that follow the Rules of React, manual memoization becomes largely unnecessary — the compiler handles it more accurately than humans do. You can opt in today in React 18 with the babel plugin. This changes the guidance: write clear, idiomatic code; let the compiler memoize; only add manual memo when the compiler cannot (impure functions, external mutation, dynamic deps).

```tsx
// With React Compiler enabled, this "just works" — no manual memo needed
function FilteredList({ items, filter }: Props) {
  const filtered = items.filter(i => i.category === filter); // compiler memoizes this
  return filtered.map(item => <Row key={item.id} item={item} />); // and this
}
```

> 💡 Senior insight: The React Compiler's output is auditable — run `npx react-compiler-healthcheck` on your codebase to see what percentage of components it can safely optimize. Components that mutate state directly or violate Rules of React are skipped.

### Q: What are reference stability patterns without memoization?

```tsx
// 1. Module-level constants: stable by definition
const EMPTY_ARRAY: Item[] = [];

function List({ items = EMPTY_ARRAY }: Props) { /* ... */ }

// 2. Colocate event handlers that don't need closure over state
const handleClick = () => console.log("clicked"); // outside component

// 3. useReducer dispatches are stable references — prefer over multiple callbacks
function Counter() {
  const [state, dispatch] = useReducer(reducer, initialState);
  // dispatch is stable; no useCallback needed when passing to children
  return <Controls onIncrement={() => dispatch({ type: "increment" })} />;
}
```

**Follow-ups they'll ask:**
- Has the React Compiler shipped? (Available in React 19, opt-in for React 18)
- How do you verify the compiler is working on a component?
- When would you still write `useMemo` in a compiler-enabled codebase?

---

## Component-Level Patterns

### Q: How do you limit re-render scope through component design?

Three patterns before reaching for memoization:

**1. Colocate state** — move state down to the component that owns it so sibling trees don't re-render.

```tsx
// Bad: top-level state causes entire tree to re-render on hover
function App() {
  const [hovered, setHovered] = useState(false);
  return <><HoverTarget onHover={setHovered} /><ExpensiveSection /></>;
}

// Good: encapsulate hover state in its own component
function HoverTarget() {
  const [hovered, setHovered] = useState(false);
  return <div onMouseEnter={() => setHovered(true)}>...</div>;
}
```

**2. Lift content up via children** — pass JSX as `children` or render props so the parent doesn't re-render the expensive subtree.

```tsx
// Bad: SlowComponent re-renders whenever ColorPicker state changes
function App() {
  const [color, setColor] = useState("red");
  return (
    <div style={{ color }}>
      <ColorPicker onChange={setColor} />
      <SlowComponent /> {/* re-renders on every color change */}
    </div>
  );
}

// Good: SlowComponent is owned by a parent that never re-renders
function App() {
  return <ColorWrapper><SlowComponent /></ColorWrapper>;
}

function ColorWrapper({ children }: { children: ReactNode }) {
  const [color, setColor] = useState("red");
  return (
    <div style={{ color }}>
      <ColorPicker onChange={setColor} />
      {children} {/* children prop is a stable reference — no re-render */}
    </div>
  );
}
```

**3. Composition over context for perf** — Context re-renders all consumers when value changes. Split context by update frequency or use a state manager with selector support.

```tsx
// Split into stable (auth) and volatile (theme) contexts
const AuthContext = createContext<User | null>(null);   // changes rarely
const ThemeContext = createContext<Theme>("light");     // changes on toggle only
```

> 💡 Senior insight: The "lift content up" pattern is the most underused performance technique in React. It's zero-cost, requires no memoization, and solves a large class of unnecessary re-renders that memo would only partially address.

---

## List Virtualization

### Q: When do you virtualize a list and what are the trade-offs?

**When:** Lists exceeding ~200-500 DOM nodes where the user observably scrolls. Measure first — DevTools Performance panel will show paint/layout costs spiking.

**react-window** (lighter, mature) vs **@tanstack/react-virtual** (headless, flexible, active development).

```tsx
import { useVirtualizer } from "@tanstack/react-virtual";

function VirtualList({ items }: { items: Item[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 60, // estimated row height in px
    overscan: 5,            // render 5 rows beyond viewport edge
  });

  return (
    <div ref={parentRef} style={{ height: 600, overflow: "auto" }}>
      <div style={{ height: virtualizer.getTotalSize(), position: "relative" }}>
        {virtualizer.getVirtualItems().map(virtualItem => (
          <div
            key={virtualItem.key}
            style={{
              position: "absolute",
              top: virtualItem.start,
              width: "100%",
            }}
          >
            <Row item={items[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Trade-offs:**
- Find-in-page (Ctrl+F) only searches rendered DOM — virtualized items are invisible to it.
- Accessibility: screen readers rely on DOM presence; off-screen items may be missed.
- Variable-height rows require `measureElement` and complicate implementation.
- Adds complexity; don't reach for it until you've measured the actual DOM node count as the bottleneck.

⚠️ Gotcha: `estimateSize` that's too inaccurate causes scroll position jumps when actual sizes differ. Always implement `measureElement` for variable-height content.

---

## Code Splitting

### Q: How do you approach code splitting in a React app?

**Route-based splitting** is the highest-leverage starting point — users only need code for the route they're on.

```tsx
import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Settings = lazy(() => import("./pages/Settings"));

function App() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}
```

**Component-based splitting** for heavy components loaded conditionally (rich text editor, chart library, map):

```tsx
const RichEditor = lazy(() => import("./RichEditor"));

function PostForm({ isEditing }: { isEditing: boolean }) {
  return isEditing ? (
    <Suspense fallback={<EditorSkeleton />}>
      <RichEditor />
    </Suspense>
  ) : (
    <StaticPreview />
  );
}
```

**Prefetching** — preload on hover/focus before the user clicks:

```tsx
const prefetchDashboard = () => import("./pages/Dashboard");

<Link
  to="/dashboard"
  onMouseEnter={prefetchDashboard}
  onFocus={prefetchDashboard}
>
  Dashboard
</Link>
```

**Bundle analysis:**
```bash
# Vite
npx vite-bundle-visualizer

# Webpack
npx webpack-bundle-analyzer stats.json

# Source-map-explorer (framework-agnostic)
npx source-map-explorer build/static/js/*.js
```

> 💡 Senior insight: Analyze your bundle *before* splitting. `source-map-explorer` will show you which dependencies are largest. Often a single lodash or moment.js import dwarfs all your application code — fix the dependency problem before splitting routes.

---

## Bundle Size

### Q: What are the most impactful bundle size optimizations?

**Tree-shaking** requires ES module syntax (`import/export`) and a bundler that supports it (Vite, webpack 5, Rollup). CommonJS (`require`) is not tree-shakeable.

```ts
// Bad: imports entire lodash (70KB+ gzipped)
import _ from "lodash";
const debounced = _.debounce(fn, 300);

// Good: import specific function (1KB)
import debounce from "lodash/debounce";

// Better: use native or tiny alternative
const debounced = useMemo(() => debounce(fn, 300), [fn]);
```

**Barrel file pitfall:** `index.ts` re-exporting everything defeats tree-shaking in many bundlers because the entire barrel is treated as one module.

```ts
// Bad: importing from barrel pulls in entire module
import { Button } from "@/components"; // loads every component

// Good: import directly
import { Button } from "@/components/Button";
```

**`sideEffects` in package.json:** mark your package as side-effect-free so bundlers can tree-shake aggressively.

```json
{ "sideEffects": ["*.css", "*.scss"] }
```

**Modern bundlers:**
- **Vite**: esbuild for dev (fast transforms), Rollup for production (optimal tree-shaking).
- **SWC**: Rust-based Babel replacement, 20-70x faster compilation.
- **esbuild**: JavaScript/Go, extremely fast but less plugin ecosystem.

> 💡 Senior insight: Use `bundlephobia.com` before adding any dependency. Check "tree-shakeable" and "has side effects" flags. A 50KB gzipped dependency added thoughtlessly undoes significant splitting work.

⚠️ Gotcha: Some libraries mark `sideEffects: false` incorrectly in their package.json, causing their CSS or polyfills to be dropped. Always verify visually after upgrading such dependencies.

---

## Network & Data

### Q: How do you diagnose and fix network performance problems in a React app?

**Waterfall problem** — sequential fetches that could be parallel:

```tsx
// Bad: waterfall — user waits for both sequentially
function Profile({ userId }: { userId: string }) {
  const { data: user } = useQuery({ queryKey: ["user", userId], queryFn: fetchUser });
  const { data: posts } = useQuery({
    queryKey: ["posts", userId],
    queryFn: fetchPosts,
    enabled: !!user, // ← this creates the waterfall
  });
}

// Good: parallel fetches
function Profile({ userId }: { userId: string }) {
  const userQuery = useQuery({ queryKey: ["user", userId], queryFn: fetchUser });
  const postsQuery = useQuery({ queryKey: ["posts", userId], queryFn: fetchPosts });
  // both fire immediately
}
```

**TanStack Query caching:**

```tsx
const { data } = useQuery({
  queryKey: ["users"],
  queryFn: fetchUsers,
  staleTime: 5 * 60 * 1000,  // data fresh for 5 min — no refetch on mount
  gcTime: 10 * 60 * 1000,    // keep in cache for 10 min after last subscriber
});
```

**Debouncing search inputs:**

```tsx
function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}
```

**Image optimization checklist:**
- Use `next/image` or equivalent — it generates responsive srcsets, serves WebP/AVIF automatically, and lazy-loads by default.
- Explicit `width` and `height` on every image to prevent CLS.
- `loading="lazy"` for below-the-fold images; never lazy-load LCP image.
- Serve AVIF (best compression) with WebP fallback.
- CDN with immutable cache headers for fingerprinted assets.

**Font loading:**
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preload" as="font" href="/fonts/inter.woff2" crossorigin>
```
Use `font-display: swap` to avoid invisible text during font load (improves FCP).

> 💡 Senior insight: In React apps using RSC, you can move data fetching to the server component — eliminating client waterfalls entirely because the server can fetch in parallel and the client receives rendered HTML with data already embedded.

---

## Rendering Strategy Impact

### Q: How do different rendering strategies affect performance?

See file 08 for deep architectural coverage. Performance summary:

| Strategy | LCP | INP | TTFB | JS Payload |
|----------|-----|-----|------|-----------|
| CSR | Poor (blank shell) | Good | Fast | Large |
| SSR | Good | Good | Medium | Large |
| Streaming SSR | Best | Good | Fast (shell) | Large |
| RSC | Best | Good | Fast | Reduced |
| Static (SSG) | Best | Good | Fastest | Depends |

**Hydration cost:** SSR ships HTML but must re-attach React event handlers on the client ("hydration"). This blocks interactivity — a large SSR'd page can have good LCP but terrible INP if hydration takes 3s.

**Partial hydration / Islands architecture** (Astro, fresh): ship zero JS for static regions, hydrate only interactive islands. Dramatically reduces main-thread work.

**Streaming SSR** (React 18+): flush the HTML shell immediately, stream in Suspense boundaries as data resolves. Improves TTFB and LCP without waiting for all data.

```tsx
// Shell renders immediately; Comments streams in when data is ready
export default function Page() {
  return (
    <Layout>
      <Article />           {/* renders synchronously */}
      <Suspense fallback={<CommentsSkeleton />}>
        <Comments />        {/* streams in asynchronously */}
      </Suspense>
    </Layout>
  );
}
```

---

## Long Tasks & Main Thread

### Q: How do you keep the main thread responsive under heavy work?

**Long tasks** are JS tasks >50ms. They block painting, delay input handling, and hurt INP.

**useTransition / useDeferredValue** (see file 05) — mark state updates as non-urgent so React can yield to user input:

```tsx
const [isPending, startTransition] = useTransition();

startTransition(() => {
  setExpensiveFilter(newValue); // React can interrupt this for urgent updates
});
```

**Web Workers** — move CPU-heavy work off the main thread entirely:

```tsx
// worker.ts
self.onmessage = (e: MessageEvent<number[]>) => {
  const result = heavyComputation(e.data);
  self.postMessage(result);
};

// component
const workerRef = useRef<Worker>();
useEffect(() => {
  workerRef.current = new Worker(new URL("./worker.ts", import.meta.url));
  workerRef.current.onmessage = (e) => setResult(e.data);
  return () => workerRef.current?.terminate();
}, []);
```

**Breaking up work** — yield to the browser between chunks using `scheduler.yield()` (or `setTimeout(0)` fallback):

```tsx
async function processChunks(items: Item[]) {
  const CHUNK_SIZE = 100;
  for (let i = 0; i < items.length; i += CHUNK_SIZE) {
    processChunk(items.slice(i, i + CHUNK_SIZE));
    await scheduler.yield(); // let browser paint/handle input between chunks
  }
}
```

**requestIdleCallback** — defer non-critical work (analytics, prefetch) to browser idle time:

```tsx
useEffect(() => {
  const id = requestIdleCallback(() => prefetchRelatedContent(articleId));
  return () => cancelIdleCallback(id);
}, [articleId]);
```

> 💡 Senior insight: `scheduler.yield()` is the modern replacement for `setTimeout(0)` with better priority semantics. It's available in Chrome 115+ and the `scheduler` polyfill covers older browsers. Prefer it over `setTimeout` for chunked processing patterns.

---

## Memory

### Q: What causes memory leaks in React and how do you detect them?

See file 01 for closure/lifecycle deep dive. Performance-specific summary:

**Common leak sources:**
- Event listeners added without cleanup: `window.addEventListener` in `useEffect` without corresponding `removeEventListener` in cleanup.
- Timers: `setInterval` without `clearInterval` in cleanup.
- Closures holding stale component state after unmount.
- Accumulating cache with no eviction (storing unlimited query results in module-level Map).

```tsx
// Leak: listener added on every render, never removed
useEffect(() => {
  window.addEventListener("resize", handleResize);
  // missing return () => window.removeEventListener("resize", handleResize);
});

// Fixed
useEffect(() => {
  window.addEventListener("resize", handleResize);
  return () => window.removeEventListener("resize", handleResize);
}, [handleResize]);
```

**Detection:** Chrome DevTools Memory tab → Take Heap Snapshot before and after an interaction. Detached DOM nodes and growing retained sizes across snapshots indicate leaks.

**Large caches:** TanStack Query's `gcTime` evicts unused cache entries. Module-level Maps or Sets for memoization need manual eviction strategy (LRU, WeakMap for object keys).

---

## Diagnostic Script: "The Dashboard is Janky"

### Q: Walk me through diagnosing a slow, janky dashboard.

This is a common senior/lead interview scenario. Structure your answer around hypotheses → measurement → fix → verify.

**Step 1 — Reproduce and characterize**
- Is it jank on load, or jank during interaction?
- Consistent or intermittent? What's the user action that triggers it?
- Any correlation with data volume (more rows = worse)?

**Step 2 — Measure load performance**
- Open Chrome DevTools → Performance tab → record page load.
- Check: LCP timing, long tasks during load, JS parse/execute cost.
- Run Lighthouse; note Core Web Vitals scores and "avoid large JS payloads" opportunities.
- `source-map-explorer` on the bundle — is a vendor library bloating it?

**Step 3 — Measure interaction performance**
- Performance tab → record the janky interaction.
- Look for long tasks (red triangles) coinciding with the interaction.
- React DevTools Profiler → record same interaction → find which components re-render and how long.
- Enable "Record why each component rendered" — is a context change triggering unnecessary renders?

**Step 4 — Form hypothesis**
Common culprits in order of frequency:
1. **Too many re-renders** — a top-level context or state update cascades through entire tree.
2. **Expensive render** — a single component doing heavy computation on every render (missing memoization, or wrong memoization).
3. **Network waterfall** — sequential data fetches delaying First Meaningful Paint.
4. **Bundle bloat** — massive initial JS causing long parse/compile blocking interactivity.
5. **Large DOM** — thousands of nodes causing slow paint/layout.
6. **Main-thread long task** — synchronous computation during event handler blocking INP.

**Step 5 — Apply targeted fix**

| Hypothesis | Fix |
|-----------|-----|
| Re-render cascade from context | Split context, use selector pattern, or use Zustand/Jotai |
| Expensive render per item | Virtualize list, memoize item component |
| Network waterfall | Parallelize fetches, prefetch on route enter, move to RSC |
| Bundle bloat | Route-split, audit dependencies, lazy-load heavy components |
| Large DOM | Virtualization |
| Long task on interaction | useTransition, break up work, Web Worker |

**Step 6 — Verify**
Re-run Profiler and Performance panel. Compare flame graphs before/after. Check Core Web Vitals in field data after deploying (CrUX data updates weekly).

> 💡 Senior insight: Frame your answer around "I'd start by measuring X to confirm the hypothesis before writing any code." Interviewers want to hear you resist the urge to immediately add `useMemo` everywhere.

---

## ⚡ Rapid-Fire

**Q: What's the first thing you check when a React app is slow?**
React DevTools Profiler — how many components are re-rendering per interaction and what's triggering them.

**Q: Does `React.memo` prevent re-renders if a prop is a function?**
No. Functions are recreated each render, producing new references. Pair memo with `useCallback` (or React Compiler).

**Q: What replaced FID in Core Web Vitals?**
INP (Interaction to Next Paint), in March 2024. INP measures full interaction latency, not just the delay before the first handler.

**Q: What's the barrel file problem?**
Re-exporting everything through an `index.ts` can prevent tree-shaking, causing unused code to appear in the bundle.

**Q: When does `useMemo` have negative ROI?**
When the computation is cheaper than the comparison React does to decide whether to recompute. Anything under ~1ms on fast hardware is likely not worth memoizing manually.

**Q: How does Streaming SSR improve performance?**
It flushes an HTML shell immediately (good TTFB), then streams Suspense boundaries as data resolves (good LCP), without waiting for all async data before sending any bytes.

**Q: What does the React Compiler change about memo?**
It auto-applies memoization equivalent to `memo`/`useMemo`/`useCallback` for components that follow the Rules of React — removing the need for most manual memoization.

**Q: How do you detect a memory leak in a React app?**
Chrome DevTools Memory tab → Heap Snapshot before/after repeated interaction → look for growing retained size and detached DOM nodes.

**Q: What's the difference between `staleTime` and `gcTime` in TanStack Query?**
`staleTime`: how long data is considered fresh (no refetch). `gcTime`: how long unused cache entries stay in memory before garbage collection.

**Q: When would you use a Web Worker in a React app?**
CPU-intensive work that would block the main thread for >50ms — e.g., parsing large CSV, running ML inference, complex data transformation.

---

## 🚩 Red Flags

- **Wrapping every component in `React.memo` by default** — signals cargo-cult optimization; no measurement, no targeted fix.
- **Adding `useMemo` to trivial values** — `useMemo(() => a + b, [a, b])` has more overhead than the computation it "optimizes."
- **"I'll optimize it later"** — performance needs to be considered at architecture time (rendering strategy, data fetching patterns).
- **Conflating re-renders with slowness** — React re-renders are cheap if the render function is cheap; not all re-renders need to be prevented.
- **Optimizing without before/after metrics** — no baseline means no proof the change helped or didn't regress something else.
- **Ignoring field data** — optimizing Lighthouse score without checking CrUX or RUM data misses real-user conditions.
- **Lazy-loading the LCP image** — explicit anti-pattern; delays the most important paint.
- **Sequential fetches without measuring** — assuming a waterfall is the problem without profiling the network tab.
- **Virtualization as the first answer for any list** — adds complexity and accessibility challenges; only warranted after measuring DOM size as the confirmed bottleneck.
- **Ignoring INP** — still thinking FID is the interaction metric; INP replaced it in 2024 and is far stricter.
