# Browser Internals: The Layer Beneath React

The browser's rendering pipeline is the foundation every React performance decision builds on. Understanding why `transform` beats `top`, why layout thrashing kills frame rates, and how storage APIs differ gives you the mental model to debug real-world perf issues — not just guess. This guide covers the Critical Rendering Path, reflow/repaint/composite costs, browser storage, service workers, and networking — everything a senior needs to reason about the platform React runs on.

---

## Critical Rendering Path (CRP)

### Q: Walk me through the full browser rendering pipeline from raw bytes to pixels.

The CRP is a waterfall of sequential steps — each stage gates the next, so any bottleneck delays the first paint.

**Steps in order:**

1. **Bytes → Characters → Tokens → Nodes → DOM**  
   The HTML parser reads bytes, tokenises tags, and builds the DOM tree. This is incremental — the parser emits nodes as it goes.

2. **CSS → CSSOM**  
   CSS files are fetched and parsed into the CSS Object Model. Unlike DOM construction, CSSOM is **not** incremental — the browser must have the full CSS before building it, because a later rule can override an earlier one.

3. **DOM + CSSOM → Render Tree**  
   Only visible nodes are included (`display: none` nodes are excluded; `visibility: hidden` nodes remain). Each render-tree node has its computed styles.

4. **Layout (Reflow)**  
   The browser walks the render tree and calculates exact positions and dimensions. Output is a box model for every node.

5. **Paint**  
   The browser converts layout boxes into pixel instructions, organized in layers (drawing order, colors, shadows, text).

6. **Composite**  
   The compositor thread assembles the painted layers and sends them to the GPU for display. This is the only step that can run off the main thread.

**What blocks rendering:**

- **Render-blocking CSS**: `<link rel="stylesheet">` blocks `Render Tree` construction. Nothing paints until CSSOM is ready.
- **Parser-blocking JS**: a classic `<script>` tag (no `async`/`defer`) halts HTML parsing, fetches the script, executes it (which may query/mutate the DOM), then resumes parsing.

```html
<!-- BLOCKS parsing — bad for CRP -->
<script src="analytics.js"></script>

<!-- Does NOT block parsing — downloaded in parallel, executes after parse -->
<script src="analytics.js" defer></script>

<!-- Does NOT block parsing — executes as soon as downloaded (order not guaranteed) -->
<script src="analytics.js" async></script>

<!-- ES module — defer by default -->
<script type="module" src="app.js"></script>
```

**CRP optimizations:**

```html
<!-- Critical CSS inlined — no extra round trip -->
<style>
  .hero { color: #333; font-size: 2rem; }
</style>

<!-- Preconnect to third-party origin early -->
<link rel="preconnect" href="https://fonts.googleapis.com" />

<!-- Preload hero image — highest priority fetch, doesn't block parser -->
<link rel="preload" href="/hero.webp" as="image" />

<!-- Non-critical CSS loaded without blocking -->
<link rel="stylesheet" href="non-critical.css" media="print" onload="this.media='all'" />
```

> 💡 Senior insight: The browser has a **preload scanner** — a secondary, lookahead parser that scans HTML while the primary parser is blocked (e.g., by a script) and kicks off fetches for `<link>`, `<img>`, `<script>` tags it finds ahead. Inline scripts defeat the preload scanner for everything below them.

**Follow-ups they'll ask:**
- What's the difference between `preload` and `prefetch`? (`preload` = current page, high priority; `prefetch` = next page, idle priority)
- When does `preconnect` help? (third-party origins: fonts, analytics — saves DNS + TCP + TLS time)
- Can you have render-blocking JS? (yes — any sync `<script>` without defer/async)

---

## async vs defer vs module vs Classic Script

### Q: What's the difference between async, defer, and type="module" for script loading?

| Attribute | Fetch | Execution timing | Order guaranteed |
|---|---|---|---|
| (none) | Blocks parser | Immediately after fetch | Yes |
| `async` | Parallel | Immediately after fetch | No |
| `defer` | Parallel | After HTML parsed, before `DOMContentLoaded` | Yes |
| `type="module"` | Parallel | Like `defer` (after parse) | Yes |

```html
<!-- Classic: blocks the parser, executes inline -->
<script src="critical.js"></script>

<!-- async: good for truly independent scripts (analytics, ads) -->
<script async src="analytics.js"></script>

<!-- defer: good for app code that needs the DOM but isn't critical path -->
<script defer src="app.js"></script>

<!-- module: automatically deferred, strict mode, own scope -->
<script type="module" src="main.js"></script>
```

> 💡 Senior insight: `async` can execute before `DOMContentLoaded` — if your script touches the DOM and you use `async`, it may run before the DOM is ready. `defer` is almost always the right choice for application scripts.

⚠️ Gotcha: `type="module"` scripts are always deferred — adding `defer` explicitly to a module script is redundant but harmless.

---

## Reflow vs Repaint vs Composite

### Q: What triggers each rendering stage, and what's the performance cost order?

**Cost order (most to least expensive):**

```
Layout (Reflow) > Paint (Repaint) > Composite
```

**What triggers each:**

| Stage | Triggered by | Examples |
|---|---|---|
| Layout + Paint + Composite | Geometry changes | `width`, `height`, `top`, `left`, `margin`, `padding`, `font-size` |
| Paint + Composite | Visual changes (no geometry) | `color`, `background-color`, `box-shadow`, `border-color` |
| Composite only | Transform/opacity | `transform`, `opacity` |

```css
/* EXPENSIVE — triggers layout on every frame */
.moving-element {
  position: absolute;
  left: calc(var(--x) * 1px); /* forces layout */
  top: calc(var(--y) * 1px);
}

/* CHEAP — compositor-only, GPU-accelerated */
.moving-element {
  transform: translate(var(--x-px), var(--y-px)); /* no layout, no paint */
  opacity: 0.9; /* also compositor-only */
}
```

**GPU/Compositor layers:**

The compositor thread promotes elements to their own **compositor layer** when it detects they'll animate. This allows those elements to be moved/faded without touching the main thread. Layers are composited (combined) by the GPU.

```css
/* Hint to the browser: promote this element to its own compositor layer */
.animated-card {
  will-change: transform;
}

/* Equivalent older hack (creates a layer by forcing GPU compositing) */
.animated-card {
  transform: translateZ(0);
}
```

⚠️ Gotcha: `will-change` has a real memory cost — each compositor layer consumes VRAM. Applying `will-change: transform` to hundreds of elements (e.g., inside `*` or a long list) can crash low-end devices. Promote layers surgically, and remove `will-change` after animation ends if possible.

> 💡 Senior insight: You can inspect compositor layers in Chrome DevTools → Layers panel. Look for "paint flashing" (highlight repaints in green) and the FPS meter under Rendering to see what's actually happening.

**Follow-ups they'll ask:**
- What creates a new stacking context? (`position` + `z-index`, `opacity < 1`, `transform`, `filter`, `isolation: isolate`)
- Does `will-change` guarantee a compositor layer? (no — it's a hint; the browser may ignore it if it has no budget)

---

## Layout Thrashing

### Q: What is layout thrashing and how do you fix it?

**Forced synchronous layout** happens when JavaScript reads a geometric property (triggering layout flush) immediately after writing a style (invalidating layout). The browser is forced to synchronously complete layout mid-frame to return a fresh value. In a loop, this causes cascading forced layouts.

**Buggy example — reads and writes interleaved:**

```typescript
// LAYOUT THRASHING — each read forces a layout flush
const boxes = document.querySelectorAll<HTMLElement>('.box');

boxes.forEach((box) => {
  const width = box.offsetWidth; // READ — forces layout
  box.style.width = `${width * 2}px`; // WRITE — invalidates layout
  // next iteration: READ again → forces another layout → ...
});
```

**Fixed — batch reads, then writes:**

```typescript
// CORRECT — all reads first, then all writes
const boxes = Array.from(document.querySelectorAll<HTMLElement>('.box'));

// Phase 1: read all values (one layout flush)
const widths = boxes.map((box) => box.offsetWidth);

// Phase 2: write all values (one layout invalidation, flushed next frame)
boxes.forEach((box, i) => {
  box.style.width = `${widths[i] * 2}px`;
});
```

**Using requestAnimationFrame for visual updates:**

```typescript
// rAF fires just before the browser paints — ideal for visual mutations
function animateBox(el: HTMLElement, targetX: number) {
  requestAnimationFrame(() => {
    el.style.transform = `translateX(${targetX}px)`;
    // Reads here are safe — we're at the start of a new frame
  });
}
```

**FastDOM pattern (library approach):**

The FastDOM library formalises read/write batching by scheduling all reads together in rAF's "measure" phase and writes in the "mutate" phase:

```typescript
// Conceptual FastDOM pattern (without the library):
const reads: (() => void)[] = [];
const writes: (() => void)[] = [];

function measure(fn: () => void) { reads.push(fn); scheduleFlush(); }
function mutate(fn: () => void) { writes.push(fn); scheduleFlush(); }

function scheduleFlush() {
  requestAnimationFrame(() => {
    reads.forEach(fn => fn());   // all reads
    reads.length = 0;
    writes.forEach(fn => fn());  // then all writes
    writes.length = 0;
  });
}
```

⚠️ Gotcha: Properties that trigger forced layout include `offsetWidth`, `offsetHeight`, `offsetTop`, `offsetLeft`, `scrollTop`, `scrollLeft`, `clientWidth`, `clientHeight`, `getBoundingClientRect()`, `getComputedStyle()`. Avoid reading these inside loops that also mutate styles.

> 💡 Senior insight: This is exactly why React batches state updates — instead of flushing DOM writes on every `setState`, it accumulates all mutations and applies them in one pass, which minimises layout thrashing at the framework level.

---

## Connecting to React & the Event Loop

### Q: How does the browser rendering pipeline explain React's design choices?

**React batching = avoiding layout thrashing at scale.**  
When multiple `setState` calls happen in a single event handler, React defers DOM mutations and flushes them together. Without this, each state update would trigger its own layout + paint cycle.

**Why `transform` beats `top`/`left` for animations:**  
Animating `top`/`left` triggers layout → paint → composite on every frame (60fps = 60 reflows/sec). Animating `transform` skips to composite-only — zero main-thread cost per frame. This is why framer-motion and CSS animation libraries default to `transform` for movement.

```typescript
// React animation anti-pattern — triggers layout every render
const [pos, setPos] = useState(0);
// <div style={{ top: pos }} />  ← layout on every setState

// Correct — compositor-only
// <div style={{ transform: `translateY(${pos}px)` }} />
```

**The main thread is shared:**  
JavaScript execution, style calculation, layout, paint preparation — all happen on the **main thread**. Long JS tasks block the browser from painting. React Concurrent Mode (see file 05) uses `scheduler` to yield the main thread between render chunks, allowing the browser to paint frames between work units. This is why `startTransition` prevents jank during expensive renders.

**Browser task/rendering loop:**

```
[Task] → [Microtasks] → [rAF callbacks] → [Style/Layout/Paint] → [Composite] → [next Task]
```

- `requestAnimationFrame` fires **before** paint — safe for style mutations.
- `requestIdleCallback` fires **after** paint, during idle — safe for non-urgent work.
- Long tasks (>50ms) block the rendering step → visible jank (>16.6ms per frame at 60fps).

> 💡 Senior insight: A 100ms synchronous JS task means the browser hasn't painted in 6+ frames. The user sees a frozen UI. React's concurrent renderer breaks work into small chunks and yields so the browser can paint at each 16.6ms budget boundary.

---

## Browser Storage Deep Dive

### Q: Walk me through all browser storage options and when you'd use each.

**Decision table:**

| Storage | Size | Sync? | Persistence | Queryable | Send to server |
|---|---|---|---|---|---|
| Cookie | ~4KB | Sync | Configurable | No | Yes (auto) |
| localStorage | 5–10MB | Sync (blocking) | Until cleared | No | No |
| sessionStorage | 5–10MB | Sync | Tab lifetime | No | No |
| IndexedDB | Hundreds MB | Async | Until cleared | Yes (indexes) | No |
| Cache API | Large (quota) | Async | Until cleared | By URL | No |

**Cookies:**

```typescript
// Set a cookie with security flags
document.cookie = "token=abc123; Secure; HttpOnly; SameSite=Strict; Max-Age=3600; Path=/";
// Note: HttpOnly cookies cannot be read by JS — only sent to the server
```

- `HttpOnly`: inaccessible to JS → mitigates XSS cookie theft
- `Secure`: HTTPS only
- `SameSite=Strict`: never sent cross-site (CSRF protection)
- `SameSite=Lax`: sent on top-level navigations (good default)
- `SameSite=None; Secure`: required for cross-site embeds (iframes, third-party widgets)
- Sent on **every HTTP request** to the matching domain — keep them small

**localStorage / sessionStorage:**

```typescript
// Synchronous — blocks the main thread during read/write
localStorage.setItem('theme', 'dark');
const theme = localStorage.getItem('theme'); // string | null

// sessionStorage: same API, but scoped to a single browser tab
sessionStorage.setItem('draft', JSON.stringify({ text: 'hello' }));
```

⚠️ Gotcha: `localStorage` is synchronous and runs on the main thread. Writing large objects (or writing in a tight loop) can cause observable jank. Never store megabytes here.

**IndexedDB — when you need real storage:**

```typescript
// Async, transactional, indexed, supports structured data
const openDB = (): Promise<IDBDatabase> =>
  new Promise((resolve, reject) => {
    const req = indexedDB.open('my-app', 1);
    req.onupgradeneeded = (e) => {
      const db = (e.target as IDBOpenDBRequest).result;
      const store = db.createObjectStore('notes', { keyPath: 'id' });
      store.createIndex('by-created', 'createdAt');
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });

async function saveNote(db: IDBDatabase, note: { id: string; text: string; createdAt: number }) {
  return new Promise<void>((resolve, reject) => {
    const tx = db.transaction('notes', 'readwrite');
    tx.objectStore('notes').put(note);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}
```

Use IndexedDB for: offline-capable apps, large datasets, structured querying, background sync data.

**Cache API (Service Worker storage):**

```typescript
// Cache HTTP responses by URL — ideal for assets and API responses
async function cacheFirst(request: Request): Promise<Response> {
  const cache = await caches.open('v1');
  const cached = await cache.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  cache.put(request, response.clone());
  return response;
}
```

**Storage quotas:**

```typescript
// Check how much quota you have and how much you've used
const estimate = await navigator.storage.estimate();
console.log(`Used: ${estimate.usage} / ${estimate.quota} bytes`);

// Request persistent storage (won't be evicted under pressure)
const granted = await navigator.storage.persist();
```

> 💡 Senior insight: Under storage pressure (low disk), browsers evict temporary storage in LRU order — IndexedDB and Cache API data can disappear without warning unless you call `navigator.storage.persist()`. Cookies and localStorage are not evicted automatically.

**Security implications:**
- XSS can read `localStorage`, `sessionStorage`, and non-`HttpOnly` cookies.
- `HttpOnly` cookies are the only storage XSS cannot touch — prefer them for auth tokens.
- Cross-origin storage is fully isolated (same-origin policy).

---

## Service Workers & PWA Basics

### Q: What is a service worker and what are the main caching strategies?

A service worker is a JavaScript file that runs in a background thread, separate from the page. It acts as a programmable network proxy — intercepting fetch requests and deciding how to respond.

**Lifecycle:**

```
Install → Activate → (fetch/message/push events)
```

```typescript
// sw.ts — registered from the main page
self.addEventListener('install', (event: ExtendableEvent) => {
  event.waitUntil(
    caches.open('v1').then(cache =>
      cache.addAll(['/index.html', '/app.js', '/styles.css'])
    )
  );
});

self.addEventListener('activate', (event: ExtendableEvent) => {
  // Clean up old caches
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== 'v1').map(k => caches.delete(k)))
    )
  );
});
```

**Caching strategies:**

| Strategy | When to use |
|---|---|
| Cache-first | Static assets, images — serve from cache, fall back to network |
| Network-first | API responses where freshness matters — try network, fall back to cache |
| Stale-while-revalidate | Balanced — serve cache immediately, revalidate in background |
| Network-only | Auth endpoints — never serve stale data |

```typescript
self.addEventListener('fetch', (event: FetchEvent) => {
  // Stale-while-revalidate for API responses
  event.respondWith(
    caches.open('api-cache').then(async (cache) => {
      const cached = await cache.match(event.request);
      const networkFetch = fetch(event.request).then((response) => {
        cache.put(event.request, response.clone());
        return response;
      });
      return cached ?? networkFetch;
    })
  );
});
```

> 💡 Senior insight: A new service worker won't take control until all tabs using the old version are closed (or you call `skipWaiting()`). This is why PWA updates can feel delayed — users on the old SW keep the old cache until they refresh after close.

---

## Networking Fundamentals

### Q: What should a senior frontend engineer know about HTTP versions, caching, and resource hints?

**HTTP/1.1 vs HTTP/2 vs HTTP/3:**

| Version | Transport | Key feature | Frontend impact |
|---|---|---|---|
| HTTP/1.1 | TCP | 6 connections per origin | Bundling, domain sharding needed |
| HTTP/2 | TCP | Multiplexing (many requests, one connection) | Bundling less critical; header compression |
| HTTP/3 | QUIC (UDP) | No head-of-line blocking, faster handshake | Lower TTFB on lossy networks |

With HTTP/2, the old advice to concatenate all JS into one bundle for fewer requests is less relevant — many smaller files can be faster (better caching granularity).

**Caching headers:**

```
# Immutable static assets (hashed filenames) — cache forever
Cache-Control: public, max-age=31536000, immutable

# HTML — always revalidate (don't cache the shell)
Cache-Control: no-cache

# API response — cache for 60s, then revalidate
Cache-Control: public, max-age=60
ETag: "abc123"
```

`ETag` enables conditional requests — browser sends `If-None-Match: "abc123"`, server returns `304 Not Modified` if unchanged → no body transfer.

**Resource hints:**

```html
<!-- DNS lookup only (cheap, use liberally) -->
<link rel="dns-prefetch" href="https://cdn.example.com" />

<!-- DNS + TCP + TLS (more expensive — use for critical third parties) -->
<link rel="preconnect" href="https://fonts.googleapis.com" crossorigin />

<!-- High-priority fetch for current page resource -->
<link rel="preload" href="/hero.webp" as="image" fetchpriority="high" />

<!-- Low-priority fetch for likely next navigation -->
<link rel="prefetch" href="/dashboard.js" />
```

**TLS/Connection setup cost (why CDN matters for LCP/TTFB):**

```
DNS lookup (~20–120ms) → TCP handshake (1 RTT) → TLS handshake (1–2 RTT) → HTTP request
```

A CDN edge node close to the user collapses this to near-zero RTT overhead — critical for LCP (Largest Contentful Paint). See file 07 for Core Web Vitals detail.

> 💡 Senior insight: `fetchpriority="high"` on the LCP image is one of the highest-ROI single-attribute changes you can make. It tells the browser to prioritise that fetch over other discovered resources, often cutting LCP by hundreds of milliseconds.

---

## Rendering Quirks: Stacking Contexts & Jank

### Q: What creates a stacking context and why does it matter for compositing?

A **stacking context** is an isolated layer in the z-axis. Elements inside cannot be z-index interleaved with elements outside:

```css
/* Each of these creates a new stacking context */
.context {
  position: relative; z-index: 1; /* or any non-auto z-index on positioned element */
  opacity: 0.99;                   /* opacity < 1 */
  transform: translateZ(0);        /* any transform */
  filter: blur(0px);               /* any filter */
  isolation: isolate;              /* explicit isolation */
  will-change: transform;          /* promotes to compositor layer */
}
```

⚠️ Gotcha: `opacity: 0.99` is a common "trick" to force GPU compositing but it creates a stacking context and a compositor layer — which consumes VRAM. Prefer `will-change: opacity` if you need the layer promotion for a known animation.

**Jank & the 16.6ms budget:**

At 60fps, the browser has 16.6ms per frame to complete: JS + style calc + layout + paint + composite. Any single step exceeding this budget causes a dropped frame — visible as jank (stuttering).

```
16.6ms budget breakdown (rough):
  JS execution:         ~4ms
  Style calculation:    ~1ms
  Layout:               ~2ms
  Paint:                ~2ms
  Composite:            ~1ms
  Browser overhead:     ~6ms
```

- Aim for JS tasks under 50ms (RAIL model)
- Use Chrome DevTools → Performance panel to record and inspect frame timelines
- The flame chart shows exactly which function pushed a frame over budget

---

## ⚡ Rapid-Fire

**Q: What's the difference between `DOMContentLoaded` and `load`?**  
`DOMContentLoaded` fires when HTML is parsed and deferred scripts run. `load` fires after all resources (images, fonts, iframes) are fetched.

**Q: Does `async` or `defer` help the preload scanner?**  
Both — the preload scanner discovers `<script src>` regardless, but `async`/`defer` prevents execution from blocking the parser.

**Q: What's the cheapest CSS animation property?**  
`opacity` and `transform` — both are compositor-only and skip layout and paint.

**Q: Can you read `localStorage` from a service worker?**  
No — service workers have no access to `localStorage` or `sessionStorage`. Use IndexedDB or Cache API.

**Q: What's `requestIdleCallback` good for?**  
Non-urgent work after paint: analytics, pre-fetching, non-critical hydration. Not appropriate for time-sensitive or visual work.

**Q: Why does `will-change: transform` on `*` hurt?**  
Each `will-change` can create a compositor layer consuming GPU memory. Promoting thousands of elements exhausts VRAM on low-end devices.

**Q: What is QUIC?**  
The UDP-based transport layer under HTTP/3. Eliminates TCP head-of-line blocking and enables 0-RTT reconnection, improving performance on mobile/lossy networks.

**Q: What triggers a reflow but NOT a repaint?**  
Nothing — reflow always causes at least a repaint of affected areas. The ordering is unidirectional: layout → paint → composite.

**Q: SameSite=Lax vs Strict for auth cookies?**  
`Lax` allows cookies on top-level GET navigations (e.g., clicking a link) — good UX. `Strict` blocks all cross-site sending — maximum CSRF protection but users lose session when arriving from external links.

**Q: What's the difference between `preload` and `prefetch`?**  
`preload`: current page, high priority, mandatory fetch. `prefetch`: future navigation, idle priority, speculative.

---

## 🚩 Red Flags

- Reading `offsetWidth` inside a loop that also sets styles — instant layout thrashing.
- Animating `top`/`left` instead of `transform: translate()` for moving elements.
- Applying `will-change: transform` to all elements globally in a stylesheet.
- Storing auth tokens in `localStorage` without understanding XSS exposure.
- Using `document.cookie` without `Secure`, `HttpOnly`, or `SameSite` flags.
- Blocking the main thread with synchronous `localStorage` writes of large objects.
- Registering a service worker without a cache invalidation strategy — users get stale assets forever.
- Using HTTP/1.1-era advice (domain sharding, excessive bundling) on an HTTP/2 CDN.
- Setting `Cache-Control: no-cache` on static hashed assets (wasted revalidation round trips).
- Not understanding that the compositor runs off the main thread — believing that "JS being busy" blocks transform animations (it doesn't, once the animation is handed off to the compositor).
- Forgetting that `sessionStorage` is per-tab — opening a link in a new tab loses the session.
- Calling `navigator.storage.persist()` silently failing and assuming IndexedDB data is durable under storage pressure.
