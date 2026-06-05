# Frontend System Design

Frontend system design is increasingly the dominant evaluation axis for senior and lead React roles — it tests whether you can reason about architecture, trade-offs, and constraints across the entire client surface. This guide gives you a repeatable framework (RADIO) to drive any design interview, paired with worked examples and cross-cutting concerns you must raise unprompted to signal seniority.

---

## The RADIO Framework

Every frontend design interview follows the same underlying structure. RADIO is a mnemonic to keep you on track.

**R** — Requirements (functional + non-functional)  
**A** — Architecture (high-level components)  
**D** — Data model (client-side)  
**I** — Interface (API / data contracts)  
**O** — Optimizations and deep-dives

### How to Drive the Interview

1. **Clarify first, always.** Ask who the users are, what platforms/devices matter, scale (DAU, data volume), and whether this is greenfield or existing system. Never assume.
2. **Scope out loud.** Say which features you're prioritizing and which you're deferring. This signals you can think in iterations.
3. **Propose before going deep.** Sketch the high-level architecture before diving into any one area. Let the interviewer redirect you.
4. **Narrate trade-offs.** For every choice, briefly name the alternative and why you didn't pick it.
5. **Invite questions.** "I could go deeper on caching or virtualization — which is more interesting to you?" shows collaboration.

```
[Interview Flow]

Clarify (5 min) → High-Level Sketch (5 min) → Data Model (5 min)
       ↓
  API Design (5 min) → Optimizations (10 min) → Deep-Dives (10 min)
```

> 💡 Senior insight: Interviewers explicitly watch whether you *raise* non-functional concerns unprompted. Waiting to be asked is a mid-level signal. Raise them in the Requirements phase.

---

## Non-Functional Concerns Checklist

Raise every item in this list during Requirements. You will not have time to solve all of them — that's fine. Naming them shows senior breadth.

| Concern | What to say |
|---|---|
| Performance / Core Web Vitals | LCP, CLS, INP targets; bundle size budget |
| Accessibility | WCAG 2.1 AA, keyboard nav, screen reader, ARIA |
| i18n / l10n | RTL, locale-aware dates/numbers, string extraction |
| Responsive | Mobile-first breakpoints, touch targets |
| Security | XSS prevention, CSP, auth token handling, CSRF |
| Error handling / resilience | Error boundaries, fallbacks, retry logic |
| Observability | RUM, error tracking (Sentry), feature flags, A/B |
| SEO | Meta tags, structured data, SSR/prerender if needed |
| Offline / PWA | Service worker, cache strategy, sync queue |

⚠️ Gotcha: Do not promise to implement all of these. The signal is that you *know* they exist and can prioritize. Say "For this use case, a11y and performance are table stakes; offline is nice-to-have."

---

## Component and State Architecture at Scale

### Component API Design Principles

Good components have small, stable APIs. They are honest about what they control vs. what they delegate.

```tsx
// Too many responsibilities — leaking layout concerns
<UserCard user={user} showBorder padding="16px" onAvatarClick={...} />

// Better — composition over props explosion
<Card>
  <Card.Avatar src={user.avatar} onClick={onAvatarClick} />
  <Card.Body>
    <Card.Title>{user.name}</Card.Title>
  </Card.Body>
</Card>
```

### Compound Components

Use the Context + implicit state pattern for related UI groups (tabs, accordion, dropdown). The parent owns state; children read it via context.

```
[Tabs]
  ├─ Context: { activeTab, setActiveTab }
  ├─ Tabs.List → renders triggers, reads context
  └─ Tabs.Panel → renders content, reads context
```

> 💡 Senior insight: Compound components solve prop-drilling without lifting state all the way to a page. They also let consumers compose the DOM structure freely, which is critical for accessibility (landmark order).

### Render Props vs Hooks

Hooks have won for logic reuse. Render props still have a niche: when the consumer needs to pass JSX *into* the logic owner (e.g., a virtualized list where the row renderer is controlled externally).

### Container / State Boundaries

```
[Page / Route]
   └─ [Feature Container]          ← owns data fetching, state
        ├─ [UI Component A]        ← pure, receives props
        ├─ [UI Component B]        ← pure, receives props
        └─ [Sub-feature Container] ← owns sub-state
```

Keep UI components free of data-fetching hooks. This makes them testable, Storybook-able, and reusable.

### Feature-Based Folder Structure

```
src/
  features/
    feed/
      components/       ← UI components scoped to this feature
      hooks/            ← useInfiniteFeed, useLike
      store/            ← Zustand slice or Redux slice
      api/              ← feed.api.ts (RTK Query or react-query)
      index.ts          ← public barrel export (module boundary)
    auth/
    notifications/
  shared/
    components/         ← design system primitives
    hooks/              ← useDebounce, useIntersectionObserver
    utils/
```

Enforce module boundaries: `feed/` may not import from `notifications/` directly. Cross-feature communication goes through shared stores or events.

### Monorepo (Nx / Turborepo)

Use a monorepo when you have multiple apps sharing a design system, utilities, or types.

```
apps/
  web/
  mobile-web/
packages/
  ui/           ← shared component library
  utils/
  types/        ← shared TypeScript types
  api-client/
```

Turborepo adds build caching (local + remote). Nx adds code generation, dependency graph enforcement, and affected-only CI.

Follow-ups they'll ask:
- How do you prevent circular dependencies between packages?
- How do you version internal packages — fixed or independent?
- How do you handle breaking changes in `packages/ui`?

---

## Data Fetching Architecture

### Client vs Server Fetching

| Pattern | When to use |
|---|---|
| Client fetch (react-query / SWR) | Authenticated data, frequently updated, after hydration |
| RSC / SSR fetch | Public data, SEO-critical, initial render must not flash |
| Static (SSG/ISR) | Rarely changing public content |

### Caching Layers

```
Browser Cache (HTTP headers)
  └─ Service Worker Cache
       └─ In-memory query cache (react-query / Apollo)
            └─ Normalized store (Apollo InMemoryCache / RTK Query)
                 └─ API Server → DB
```

React Query: cache is keyed by query key, deduplicated by default, stale-while-revalidate semantics. Configure `staleTime` (how long data is fresh) and `gcTime` (how long unused cache lives).

### Normalization

For relational data (users referenced in multiple places), normalize by ID in a map. Apollo does this automatically. With React Query, do it manually or use a separate normalized cache (e.g., `normy`).

```ts
// Normalized shape
{
  users: { "u1": {...}, "u2": {...} },
  posts: { "p1": { authorId: "u1", ... } }
}
```

### Optimistic Updates

```ts
useMutation({
  mutationFn: likePost,
  onMutate: async (postId) => {
    await queryClient.cancelQueries({ queryKey: ['feed'] });
    const previous = queryClient.getQueryData(['feed']);
    queryClient.setQueryData(['feed'], (old) => optimisticToggle(old, postId));
    return { previous };
  },
  onError: (err, postId, context) => {
    queryClient.setQueryData(['feed'], context.previous);
  },
  onSettled: () => queryClient.invalidateQueries({ queryKey: ['feed'] }),
});
```

> 💡 Senior insight: Always implement the rollback path in `onError`. Optimistic updates without rollback are a reliability trap.

### Real-Time: WebSocket vs SSE vs Polling

| Mechanism | Pros | Cons | Use when |
|---|---|---|---|
| WebSocket | Full-duplex, low latency | Complex, stateful server | Chat, collaborative editing |
| SSE | Simple, HTTP, auto-reconnect | Server → client only | Feeds, notifications, progress |
| Long polling | Works everywhere, stateless | High latency, server load | Legacy fallback |
| Short polling | Simplest | Wastes requests | Low-frequency, non-critical |

### GraphQL vs REST vs tRPC

- **REST**: Universal, cacheable at HTTP layer, excellent for public APIs.
- **GraphQL**: Great when clients need flexible queries and you have many consumers. Adds complexity (N+1, schema governance, no native HTTP cache).
- **tRPC**: Best for full-stack TypeScript monorepos — end-to-end type safety with zero schema boilerplate. No good outside TS.

### Pagination Strategies

| Strategy | Pros | Cons |
|---|---|---|
| Offset (`page=2&limit=20`) | Simple, random access | Skips/duplicates on inserts, no infinite scroll |
| Cursor (`after=abc123`) | Stable, infinite scroll-friendly | No random access, hard to show "page 5 of 20" |
| Keyset (same as cursor) | Performant at scale | Same as cursor |

For feeds and infinite scroll: always use cursor pagination.

### Prefetching

Prefetch on hover (links), on route transition, or based on user intent signals.

```ts
// react-query: prefetch on hover
<Link
  onMouseEnter={() =>
    queryClient.prefetchQuery({ queryKey: ['post', id], queryFn: fetchPost })
  }
>
```

---

## Design Systems and Component Libraries

### Architecture

```
[Design Tokens]          ← color, spacing, typography, motion (JSON/CSS vars)
      ↓
[Headless Components]    ← Radix UI, Headless UI — behavior + a11y, no styles
      ↓
[Styled Layer]           ← your brand styles applied on top
      ↓
[Composed Patterns]      ← Form, DataTable, Modal assembled from primitives
```

### Tokens

Store tokens as CSS custom properties. This enables runtime theming without JS.

```css
:root {
  --color-primary-500: #3b82f6;
  --spacing-4: 1rem;
  --radius-md: 0.375rem;
}
[data-theme="dark"] {
  --color-primary-500: #60a5fa;
}
```

### Versioning and Distribution

- Publish to npm (private registry for internal libs).
- Use semantic versioning. Breaking changes = major bump.
- Use Changesets for automated changelog and version management in monorepos.
- Colocate Storybook stories with components. Chromatic for visual regression.

### Governance

- Design reviews required before adding new primitives.
- Deprecation policy: mark deprecated, provide migration guide, remove in next major.
- A11y baked in via headless layer — never ship a component without keyboard support and correct ARIA roles.

Follow-ups they'll ask:
- How do you handle a design token change that affects 50 components?
- How do you version the design system alongside consuming apps?
- How do you ensure a11y compliance at scale?

---

## Micro-Frontends

### When They Help

Conway's Law: your architecture mirrors your org structure. MFEs make sense when:
- Multiple independent teams own distinct product surfaces.
- Teams have incompatible release cadences.
- You need to migrate legacy apps incrementally.

### When They Hurt (Most Teams Should Not Use Them)

⚠️ Gotcha: MFEs add significant complexity: bundle duplication, shared dependency management, cross-MFE routing, inconsistent UX, testing surface explosion. If you have one team or one codebase, a well-structured monorepo is almost always better.

### Module Federation (Webpack 5 / Rspack)

Runtime integration: each MFE is a separate build that exposes modules. The shell (host) loads them at runtime.

```
[Shell App]  ← host
  ├─ loads → [MFE: Checkout]   (remote, own deploy)
  ├─ loads → [MFE: Product]    (remote, own deploy)
  └─ loads → [MFE: Account]    (remote, own deploy)
```

Critical problems to solve:
1. **Shared singletons**: React must be a singleton. Use `singleton: true` in Module Federation config.
2. **Routing**: Shell owns top-level routes; MFEs own nested routes.
3. **Shared state**: Use a shared event bus or a small pub/sub store — avoid importing across MFE boundaries.
4. **A11y**: Focus management across MFE boundaries is non-trivial.

> 💡 Senior insight: The main value of MFEs is *independent deployability*. If teams still coordinate releases, you get all the complexity with none of the benefit.

---

## Rendering Strategy Decision Tree

```
Is content public and SEO-critical?
  YES → Is it frequently updated?
          NO  → SSG (build-time, CDN-served)
          YES → ISR (Next.js) or SSR
  NO  → Is it behind auth?
          YES → CSR (SPA) or SSR for initial shell
          ...Is data highly personalized?
               YES → CSR or RSC streaming
               NO  → SSR with cache
```

| Strategy | TTFB | SEO | Personalized | Cost |
|---|---|---|---|---|
| CSR | High | Poor | Yes | Low |
| SSR | Low | Excellent | Yes | High |
| SSG | Lowest | Excellent | No | Lowest |
| ISR | Low | Excellent | Limited | Low |
| RSC Streaming | Low | Good | Yes | Medium |
| Islands | Low | Excellent | Selective | Low |

See file 08 for deeper rendering strategy analysis.

---

## Worked Example 1: News / Social Feed

### Requirements

**Functional:** Infinite scroll feed, post cards (image/text/video), like/comment/share, real-time new-post notification, algorithmic ordering.  
**Non-functional:** LCP < 2.5s, smooth scroll at 60fps, offline read support, a11y (keyboard nav through feed), i18n.

### Architecture

```
[Feed Page]
  ├─ [FeedContainer]          ← owns react-query infinite query
  │    ├─ [VirtualizedList]   ← react-virtual / TanStack Virtual
  │    │    └─ [PostCard]     ← pure component, receives post data
  │    └─ [NewPostsBanner]    ← SSE listener, shows "10 new posts"
  └─ [LikeButton]             ← optimistic mutation
```

### Data Model (Client)

```ts
interface Post {
  id: string;
  authorId: string;
  content: string;
  mediaUrls: string[];
  likeCount: number;
  isLikedByMe: boolean;
  createdAt: string; // ISO
  cursor: string;    // for pagination
}

interface FeedPage {
  posts: Post[];
  nextCursor: string | null;
}
```

### API / Interface

```
GET /feed?cursor=<cursor>&limit=20
  → FeedPage

POST /posts/:id/like
  ← 204

SSE /feed/events
  → { type: 'NEW_POSTS', count: 5 }
```

### Optimizations

- **Virtualization**: Only render visible rows with TanStack Virtual. Recycle DOM nodes. Estimate row heights for variable-height posts.
- **Image pipeline**: Use `srcset` + WebP, lazy-load images below fold, blur-hash placeholder while loading.
- **Real-time**: SSE for new-post count banner. On click, prepend new posts and scroll to top. Never auto-scroll — it destroys UX.
- **Optimistic likes**: Update `isLikedByMe` and `likeCount` immediately, roll back on error.
- **Offline**: Service worker caches last feed page (Cache-first for images, stale-while-revalidate for feed JSON).
- **A11y**: Feed is a `<ul role="feed">`. Each post is `<li>`. "Load more" button is keyboard-accessible. Like button toggles `aria-pressed`.

Follow-ups they'll ask:
- How do you handle cursor invalidation when new posts arrive?
- How do you prevent CLS when images load into the virtual list?
- How do you deduplicate posts that appear in both the cached page and the real-time update?

---

## Worked Example 2: Large Data Table (1M Rows)

### Requirements

**Functional:** Display tabular data with sorting, filtering, column resize, multi-row selection, row actions, export.  
**Non-functional:** Handle 1M rows without browser crash, keyboard navigable, screen reader accessible, responsive to viewport.

### Architecture

```
[DataGridPage]
  └─ [DataGridContainer]         ← query state, sort/filter params, selection state
       ├─ [Toolbar]              ← filter inputs, export button, column toggle
       ├─ [VirtualizedGrid]      ← TanStack Virtual (row + column virtualization)
       │    ├─ [HeaderRow]       ← sortable column headers, resize handles
       │    └─ [DataRow]         ← virtualized, selection checkbox
       └─ [Pagination / Count]
```

### Key Design Decisions

**Virtualization (mandatory):** Render only visible rows and columns. TanStack Virtual handles both axes. For 1M rows, pagination is still needed — virtual scroll a page of 10k at a time.

**Server-side sort/filter:** Never sort/filter 1M rows in the browser. All sort/filter/search params go to the API as query parameters. URL state keeps it shareable and refreshable.

```ts
// URL-driven state
/data?sort=name:asc&filter=status:active&page=1
```

**Column resize:** Store column widths in local state (or user preference API). Use `pointer` events on the resize handle, not `mouse` events (touch support).

**Selection at scale:** Never store "selected row objects." Store selected IDs in a `Set<string>`. Support "select all on current page" and "select all matching filter" (the latter sends a bulk operation to the API, not 1M IDs).

### A11y for Data Grids

This is where most candidates fail. Use `role="grid"`, `role="row"`, `role="gridcell"`, `role="columnheader"`. Implement arrow key navigation between cells. Announce sort state changes via `aria-sort`. Use `aria-rowcount` and `aria-rowindex` for virtual rows.

> 💡 Senior insight: ARIA grid patterns are complex. Using a headless library like TanStack Table that handles ARIA attributes is defensible. Name-dropping this shows you understand the depth of the problem.

Follow-ups they'll ask:
- How do you export 1M rows to CSV without freezing the browser?
- How do you handle column re-ordering?
- How do you persist column preferences per user?

---

## Worked Example 3: Autocomplete / Typeahead

### Requirements

**Functional:** Search suggestions as user types, keyboard navigation, recent searches, grouped results, async with debounce.  
**Non-functional:** No redundant requests, a11y (ARIA combobox pattern), works on mobile, handles network errors gracefully.

### Architecture

```
[SearchBar]
  ├─ [Input]              ← controlled, aria-combobox
  └─ [SuggestionList]     ← aria-listbox, positioned
       ├─ [SuggestionGroup: Recent]
       └─ [SuggestionGroup: Results]
```

### Data Flow

```
User types
  → debounce(300ms)
  → cancel in-flight request (AbortController)
  → fetch /suggest?q=<term>
  → cache result by query string (react-query or local Map)
  → render suggestions
```

```ts
const controller = useRef<AbortController | null>(null);

const fetchSuggestions = async (query: string) => {
  controller.current?.abort();
  controller.current = new AbortController();

  return fetch(`/suggest?q=${query}`, {
    signal: controller.current.signal,
  }).then(r => r.json());
};
```

### Caching Strategy

Cache results in a `Map<string, Suggestion[]>` keyed by normalized query. LRU eviction at 100 entries. This makes backspace fast — no re-fetch.

### A11y: ARIA Combobox Pattern

```html
<input
  role="combobox"
  aria-expanded="true"
  aria-controls="suggestion-list"
  aria-activedescendant="suggestion-3"
  aria-autocomplete="list"
/>
<ul id="suggestion-list" role="listbox">
  <li id="suggestion-1" role="option" aria-selected="false">...</li>
  <li id="suggestion-3" role="option" aria-selected="true">...</li>
</ul>
```

Keyboard: Arrow keys move `aria-activedescendant`. Enter selects. Escape closes and returns focus to input.

Follow-ups they'll ask:
- How do you handle the case where the debounced fetch completes out of order?
- How do you rank results — client-side re-ranking vs. server-side?
- How do you instrument which suggestions users actually click?

---

## Worked Example 4 (Sketch): Collaborative Editor

**Use case:** Google Docs-style real-time co-editing with presence indicators.

**Core challenge:** Concurrent edits from multiple users must converge to the same document state.

**Approach options:**
- **OT (Operational Transformation)**: Used by Google Docs. Complex to implement correctly. Server coordinates.
- **CRDT (Conflict-free Replicated Data Types)**: Used by Figma (Yjs library). Peers can sync directly. Yjs + WebSocket is the practical choice for new systems.

**High-level architecture:**
```
[Editor Client A] ──WebSocket──┐
[Editor Client B] ──WebSocket──┤── [Collab Server (Y-websocket)] ── [Yjs Doc Store]
[Editor Client C] ──WebSocket──┘
```

**Presence:** Awareness protocol in Yjs broadcasts cursor position and selection. Each client renders others' cursors with color-coded indicators.

**Offline:** Yjs stores pending ops locally (IndexedDB). On reconnect, it merges with server state via CRDT merge.

---

## Cross-Cutting Concerns

### Error Boundaries and Resilience

Wrap each feature in an error boundary. Never have one global boundary that kills the page.

```tsx
// Feature-level error boundary
<ErrorBoundary fallback={<FeedError />}>
  <FeedContainer />
</ErrorBoundary>
```

Layer your fallback strategy:
1. Component-level error boundary → show inline error UI
2. React Query `onError` + toast for non-fatal errors
3. Global error page only for auth failures and catastrophic errors

### Observability

- **RUM (Real User Monitoring)**: Track Core Web Vitals with `web-vitals` library. Send to DataDog/Grafana.
- **Error tracking**: Sentry with source maps. Capture component stack in error boundaries.
- **Feature flags**: LaunchDarkly / Unleash. Wrap new features in flags for safe rollout and instant kill switch.
- **A/B testing**: Use flag variants, measure conversion through analytics events.

### i18n Architecture

```
[ICU message format strings in locale files]
   ↓
[react-i18next / FormatJS]
   ↓
[Locale detection: Accept-Language header or URL prefix /fr/...]
   ↓
[Lazy load locale bundles] ← don't ship all locales in one bundle
```

Critical: externalize all user-visible strings from day one. Retrofitting i18n into a large app is extremely painful.

RTL support: use CSS logical properties (`margin-inline-start` not `margin-left`). Test with Arabic or Hebrew locale.

### Image and Media Pipeline

1. Modern formats: WebP with JPEG/PNG fallback via `<picture>`.
2. Responsive images: `srcset` with multiple resolutions.
3. Lazy loading: `loading="lazy"` for below-fold images.
4. Blur hash or LQIP (Low Quality Image Placeholder) while loading.
5. CDN with image resizing (Cloudflare Images, Imgix) — never serve original uploads directly.

### Offline / PWA / Service Workers

```
[Service Worker Strategies]

Cache-First:     Images, fonts, static assets → fast, staleness acceptable
Network-First:   API responses → fresh data preferred, fall back to cache
Stale-While-Revalidate: Feed JSON → show cached, refresh in background
Background Sync: Like/comment actions while offline → retry when reconnected
```

---

## Frontend Design Patterns

### Container / Presentational

Container: knows about data, state, side effects. Presentational: receives props, renders UI. This separation is still valuable even in a hooks world — it maps to the feature container / UI component boundary described earlier.

### HOC vs Hooks

HOCs are largely superseded. Use hooks for logic reuse. The exception: cross-cutting concerns that wrap components (error boundaries, analytics tracking HOC for legacy codebases).

### Provider Pattern

Avoid mega-providers that hold all state. Scope providers to the subtree that needs them.

```tsx
// Bad: all state in one root provider
<AppProvider> ... </AppProvider>

// Good: scoped providers
<ThemeProvider>       ← layout root
  <AuthProvider>      ← app root
    <FeedProvider>    ← feed route only
      <FeedPage />
    </FeedProvider>
  </AuthProvider>
</ThemeProvider>
```

### State Machines (XState) for Complex Flows

Use state machines for UIs with many states and transitions: multi-step forms, checkout flows, media players, authentication flows.

```
[Checkout Machine]
  idle → cart_review → address → payment → processing → success
                                              ↓
                                           error → payment (retry)
```

XState makes impossible states impossible (you cannot be in `success` and `error` simultaneously) and makes transitions explicit and testable.

> 💡 Senior insight: Knowing when NOT to use a state machine is equally important. A toggle button does not need XState. A 5-step checkout wizard does.

---

## ⚡ Rapid-Fire

**Q: When would you choose SSE over WebSocket?**  
A: When communication is server → client only. SSE is simpler, uses HTTP/2 multiplexing, and auto-reconnects. WebSocket only needed for bidirectional.

**Q: What is staleTime vs gcTime in React Query?**  
A: `staleTime`: how long data is considered fresh (no background refetch). `gcTime`: how long unused cache entries are kept before garbage collection.

**Q: How do you prevent waterfall data fetching in React?**  
A: Lift fetches to route-level loaders (React Router v6, Next.js), use parallel queries, or use RSC which can fetch in parallel on the server.

**Q: What is CLS and how do you prevent it?**  
A: Cumulative Layout Shift — elements moving after initial render. Prevent by reserving space for images (`aspect-ratio`), skeleton screens with fixed dimensions, avoiding DOM insertions above the fold.

**Q: Offset vs cursor pagination?**  
A: Offset is simple but unstable (inserts shift pages). Cursor is stable and performant. Always use cursor for infinite scroll.

**Q: How do you handle a design token change that breaks 30 components?**  
A: Update the token, run visual regression in Chromatic (Storybook), review diffs, then release as a minor version if additive or major version if breaking. Consumers pin and upgrade on their schedule.

**Q: What is Module Federation's biggest operational risk?**  
A: Version mismatch of shared singletons (React). If host and remote ship different React versions and `singleton: true` is not set, you get two React instances and hook failures.

---

## 🚩 Red Flags

- Jumping into implementation details before clarifying requirements.
- Never mentioning accessibility or treating it as an afterthought.
- Proposing to sort/filter 1M rows client-side.
- Using offset pagination for an infinite scroll feed.
- No rollback path for optimistic updates.
- Proposing micro-frontends for a single-team product.
- One global error boundary for the entire app.
- Shipping all locale bundles in the main JS chunk.
- Storing full selected objects instead of IDs in selection state.
- Not knowing the difference between `staleTime` and `gcTime` in React Query.
- Treating SSR as always better than CSR — failing to articulate trade-offs.
- No mention of observability, feature flags, or incremental rollout strategy.
