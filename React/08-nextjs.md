# Next.js — App Router, RSC, and the Full Production Mental Model

Next.js 14/15 with the App Router represents a fundamental shift in how React applications are architected — not just a routing upgrade, but a new rendering and data-fetching paradigm built on React Server Components. Senior engineers must reason fluently about what runs where, when data is cached, and how to make deliberate trade-offs between performance, freshness, and complexity. This guide covers every topic that separates a lead-level Next.js engineer from someone who just knows the file conventions.

---

## Rendering Strategies

### Q: Walk me through CSR, SSR, SSG, ISR, and streaming. When do you reach for each?

**Trade-off lens first:** Every rendering strategy is a point on the spectrum between time-to-first-byte, content freshness, infrastructure cost, and interactivity. Picking wrong means either slow initial loads or stale data — or both.

| Strategy | When HTML is generated | Data freshness | Next.js mechanism |
|---|---|---|---|
| **CSR** | In the browser | Always fresh | Client component with `useEffect`/SWR |
| **SSR** | Per request, on server | Always fresh | `async` server component (no cache config) |
| **SSG** | At build time | Stale until rebuild | `generateStaticParams` + static page |
| **ISR** | At build + background revalidation | Fresh within window | `export const revalidate = 60` |
| **Streaming** | Progressively per Suspense boundary | Per-boundary strategy | `<Suspense>` + `loading.tsx` |

**CSR:** Dashboards behind auth where SEO is irrelevant and data is user-specific. Reduces server load; poor for LCP.

**SSR (dynamic rendering):** Personalized pages, real-time stock tickers, anything reading cookies/headers at request time. Highest server cost; perfect freshness.

**SSG:** Marketing pages, docs, blog posts that change on deploy. Zero server cost; terrible for frequently-changing data.

**ISR:** Product catalogue, news feeds — data changes but not per-second. Best of SSG + approximate freshness. The background revalidation means the first visitor after expiry still sees stale content (stale-while-revalidate semantics).

**Streaming:** Long-running data fetches where you want the shell immediately. Pairs with Suspense to progressively hydrate. Critical for good TTFB on data-heavy pages.

> 💡 **Senior insight:** In App Router, dynamic vs. static rendering is determined automatically — if a component reads `cookies()`, `headers()`, or uses `fetch` with `cache: 'no-store'`, the entire route segment becomes dynamic. You don't opt in; you opt out of dynamism.

⚠️ **Gotcha:** SSG + ISR still runs server-side Node/edge code at revalidation time. "Static" means statically served, not "no server ever."

**Follow-ups they'll ask:**
- How does ISR revalidation actually work under the hood? (background fetch, atomic swap of the cached response)
- What happens during the revalidation window if the origin is down?
- How do you force a full rebuild vs. on-demand ISR?

---

## React Server Components — The Core Mental Model

### Q: Explain the RSC mental model. What is the serialization boundary and why can't you pass functions across it?

**Trade-off:** RSCs eliminate client JS for components that don't need interactivity, shrinking bundles dramatically — but they introduce a hard serialization boundary that constrains what can cross the network.

**What runs where:**

- **Server Components**: render on the server (or at build time). They can `await` database calls, read the filesystem, use secrets. They never ship their own JS to the client. They cannot use `useState`, `useEffect`, or browser APIs.
- **Client Components**: marked with `"use client"`. Rendered on the server for the initial HTML (SSR), then hydrated in the browser. They can use hooks, event handlers, browser APIs.

**The serialization boundary:** When a Server Component renders a Client Component, the props crossing that boundary must be serializable to JSON — strings, numbers, plain objects, arrays, and React elements (JSX). Functions are closures capturing server memory; they cannot be serialized and sent over the wire. This is a runtime constraint, not just a linting rule.

```tsx
// ✅ Valid — passing serializable data
// app/dashboard/page.tsx (Server Component)
import { Chart } from './Chart'; // 'use client'
import { getMetrics } from '@/lib/db';

export default async function DashboardPage() {
  const metrics = await getMetrics(); // runs on server
  return <Chart data={metrics} />;   // data is serializable
}
```

```tsx
// ❌ Invalid — passing a function across the boundary
export default async function Page() {
  const handler = () => console.log('clicked');
  return <Button onClick={handler} />; // Button is 'use client'
  // Error: Functions cannot be passed as props to Client Components
}
```

**RSC wire format (payload):** The server sends a JSON-like tree describing the rendered output — component references, props, children. Client components appear as references; the browser uses this to hydrate without re-fetching. This is separate from the HTML stream used for the initial page load.

**Interleaving server + client:** You can pass Server Components as `children` to Client Components because children are already-rendered React elements (serializable), not component types.

```tsx
// ✅ Server component as children of client component
// layout.tsx (Server Component)
import { Modal } from './Modal'; // 'use client'
import { ServerSideContent } from './ServerSideContent'; // Server Component

export default function Layout() {
  return (
    <Modal>
      <ServerSideContent /> {/* This renders on server, passed as element */}
    </Modal>
  );
}
```

> 💡 **Senior insight:** `"use client"` marks a boundary, not a file. Everything imported by a `"use client"` file also runs on the client, transitively. Keep client boundaries as deep in the tree as possible to maximise server rendering.

⚠️ **Gotcha:** Context providers must be Client Components. Wrap only the subtree that needs the context; don't wrap the entire app unless necessary.

**Follow-ups they'll ask:**
- Can a Client Component import a Server Component? (No — it would break the boundary. Composition via children/props is the pattern.)
- How does hydration work if the server rendered the component but the client needs to re-render it?
- What is the RSC payload and how does it differ from SSR HTML?

---

## App Router File Conventions

### Q: Describe the App Router file conventions and how nested layouts achieve partial rendering.

**Trade-off:** Nested layouts enable persistent UI (sidebars, nav) without full-page remounts, but add complexity to error and loading state scoping.

| File | Purpose |
|---|---|
| `layout.tsx` | Persistent shell wrapping all children; **not remounted** on navigation |
| `page.tsx` | Unique UI for a route segment; rendered inside the layout |
| `loading.tsx` | Instant loading UI via Suspense wrapper (auto-wraps `page.tsx`) |
| `error.tsx` | Error boundary for the segment; must be `"use client"` |
| `not-found.tsx` | Rendered by `notFound()` throw |
| `template.tsx` | Like layout but **remounted** on every navigation (rare use case) |
| `route.ts` | API route handler (no UI) |

**Route Groups** `(groupName)`: Organise routes without affecting the URL. Useful for sharing layouts across non-adjacent segments.

```
app/
  (marketing)/
    layout.tsx       ← marketing layout
    page.tsx         ← /
    about/page.tsx   ← /about
  (app)/
    layout.tsx       ← app layout (auth shell)
    dashboard/page.tsx ← /dashboard
```

**Parallel Routes** `@slotName`: Render multiple pages simultaneously in one layout. Used for modals, split-pane UIs, tab groups that each have their own loading/error states.

**Intercepting Routes** `(.)path`: Render a route in the context of the current layout (e.g., open a photo modal over a feed) while the full route still exists when navigated to directly.

**Partial rendering on navigation:** When navigating between sibling segments, Next.js only re-renders the changed `page.tsx` — shared parent layouts are preserved in the client cache. This is fundamentally different from Pages Router where every navigation was a full component tree swap.

> 💡 **Senior insight:** `template.tsx` forces remount; useful when you need mount-time side effects (analytics page views, form resets) per navigation, but comes at the cost of lost persistent state.

⚠️ **Gotcha:** `error.tsx` boundaries do not catch errors in the same segment's `layout.tsx`. To catch layout errors, the `error.tsx` must live in the **parent** segment.

---

## Data Fetching and Streaming

### Q: How do you handle parallel vs. sequential data fetching in Server Components, and how does Suspense + streaming fit in?

**Trade-off:** Sequential fetching is safe but creates waterfall latency. Parallel fetching via `Promise.all` removes waterfalls but loses granular streaming control. Suspense boundaries allow granular progressive rendering.

**Sequential (waterfall — avoid unless dependency exists):**
```tsx
async function Page() {
  const user = await getUser();           // wait
  const posts = await getPosts(user.id);  // then wait
  return <PostList posts={posts} />;
}
```

**Parallel (prefer when data is independent):**
```tsx
async function Page() {
  const [user, settings] = await Promise.all([
    getUser(),
    getSettings(),
  ]);
  return <Profile user={user} settings={settings} />;
}
```

**Streaming with Suspense:** Initiate the fetch, don't await at the top level — let Suspense stream the shell immediately and resolve when data arrives.

```tsx
// app/feed/page.tsx
import { Suspense } from 'react';
import { PostFeed } from './PostFeed';
import { PostFeedSkeleton } from './PostFeedSkeleton';

export default function FeedPage() {
  return (
    <main>
      <h1>Feed</h1>
      <Suspense fallback={<PostFeedSkeleton />}>
        <PostFeed /> {/* async component, fetches internally */}
      </Suspense>
    </main>
  );
}
```

```tsx
// PostFeed.tsx (Server Component)
async function PostFeed() {
  const posts = await getPosts(); // streamed when ready
  return <ul>{posts.map(p => <PostItem key={p.id} post={p} />)}</ul>;
}
```

`loading.tsx` is syntactic sugar that auto-wraps the `page.tsx` in a Suspense boundary with the loading UI — it's not magic, just convention.

> 💡 **Senior insight:** Each Suspense boundary is an independent streaming chunk. Granular boundaries improve perceived performance — the user sees a populated header before the feed resolves. But too many boundaries create layout jank; group related content.

⚠️ **Gotcha:** `error.tsx` boundaries must be Client Components (`"use client"`) because they use `useEffect` to reset state. This is enforced by the framework.

---

## The Next.js Caching Model (The Senior Trap)

### Q: Explain all four caching layers in Next.js and the Next 14 vs 15 default-caching change.

**Trade-off:** Next.js's multi-layer cache is a massive performance win by default, but it is the #1 source of "why is my data stale?" bugs. You must know which layer is responsible for each symptom.

**Four caching layers:**

**1. Request Memoization (React layer)**
- Scope: single request lifecycle (one render pass)
- What: identical `fetch()` calls with the same URL+options are deduplicated automatically via React's `cache()` wrapper
- Implication: call `getUser()` in both a layout and a page — one network request

**2. Data Cache (Next.js persistent layer)**
- Scope: persistent across requests and deployments (server-side)
- What: `fetch()` responses stored on the server by URL+options key
- Control: `fetch(url, { cache: 'force-cache' })` | `cache: 'no-store'` | `next: { revalidate: 60 }` | `next: { tags: ['products'] }`
- Survives: server restarts on Vercel (stored externally); wiped on full deploy by default

**3. Full Route Cache (Next.js build-time layer)**
- Scope: statically rendered routes cached at build time as HTML + RSC payload
- What: completely pre-rendered pages served without hitting origin
- Invalidated by: revalidation (time or tag), new deployment

**4. Router Cache (client-side)**
- Scope: browser session memory
- What: prefetched and visited route segments stored in the React tree
- Duration: 30s for static segments, 0s default in Next 15 (5m in Next 14)
- Invalidated by: `router.refresh()`, Server Action with `revalidatePath`, tab close

**The Next 14 vs 15 caching change — critical:**

| Behavior | Next 14 | Next 15 |
|---|---|---|
| `fetch` default | `force-cache` | `no-store` |
| Router Cache (dynamic) | 30s | 0s |
| `<Link>` prefetch | Full segment | Loading state only |

In Next 15, `fetch` is opt-in caching. Routes are dynamic by default unless you explicitly add `export const revalidate = 3600` or use `force-cache`. This broke many Next 14 apps silently on upgrade.

**On-demand revalidation:**
```tsx
// app/api/revalidate/route.ts
import { revalidateTag, revalidatePath } from 'next/cache';
import { NextRequest } from 'next/server';

export async function POST(req: NextRequest) {
  const { tag, path, secret } = await req.json();
  if (secret !== process.env.REVALIDATION_SECRET) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }
  if (tag) revalidateTag(tag);
  if (path) revalidatePath(path);
  return Response.json({ revalidated: true });
}
```

**Route segment config:**
```tsx
// Force dynamic for the entire route
export const dynamic = 'force-dynamic';
// Time-based ISR
export const revalidate = 60;
// Control fetch cache behaviour for all fetches in segment
export const fetchCache = 'force-no-store';
```

> 💡 **Senior insight:** Tag-based revalidation (`revalidateTag`) is far more precise than path-based. Tag your fetches at the data level (`next: { tags: ['product', `product-${id}`] }`) and invalidate surgically from Server Actions on mutation.

⚠️ **Gotcha:** The Data Cache and Router Cache are separate. Calling `revalidatePath` clears the Data Cache and Full Route Cache on the server — but the client Router Cache will still serve stale content until `router.refresh()` is called or the cache duration expires.

**Follow-ups they'll ask:**
- What is the difference between `revalidatePath` and `revalidateTag`?
- How do you opt a single `fetch` out of caching while the rest of the route is static?
- Why did the Next 15 default change cause production incidents?

---

## Server Actions

### Q: What are Server Actions, when do you use them vs. Route Handlers, and what are the security implications?

**Trade-off:** Server Actions integrate seamlessly with forms and progressive enhancement but are public HTTP endpoints — treat them exactly like API routes for authorization.

**What they are:** Async functions marked `"use server"` that execute on the server when called from Client Components or forms. Next.js generates a unique POST endpoint for each action automatically.

```tsx
// app/actions.ts
'use server';

import { revalidateTag } from 'next/cache';
import { cookies } from 'next/headers';

export async function updateProduct(formData: FormData) {
  const session = cookies().get('session')?.value;
  if (!validateSession(session)) throw new Error('Unauthorized');

  const name = formData.get('name') as string;
  await db.product.update({ where: { id: formData.get('id') }, data: { name } });
  revalidateTag('products');
}
```

```tsx
// Client Component usage
'use client';
import { updateProduct } from '../actions';

export function ProductForm({ id }: { id: string }) {
  return (
    <form action={updateProduct}>
      <input name="id" type="hidden" value={id} />
      <input name="name" placeholder="Product name" />
      <button type="submit">Save</button>
    </form>
  );
}
```

**Progressive enhancement:** Forms with `action={serverAction}` work without JavaScript — the form POSTs natively and the server responds. JS enhances by intercepting and updating UI without full reload.

**Server Actions vs Route Handlers:**

| Concern | Server Action | Route Handler |
|---|---|---|
| Forms / mutations | Primary use case | Possible but verbose |
| Third-party webhooks | Not suitable | Use route handlers |
| Streaming responses | No | Yes |
| Custom HTTP headers/status | No | Yes |
| REST/OpenAPI surface | No | Yes |

**Security:** Server Actions are POST endpoints at `/_next/action`. They're accessible from anywhere on the internet. Always validate session/auth inside the action. Never trust FormData without validation.

> 💡 **Senior insight:** Use `useActionState` (React 19) for managing pending state and errors from Server Actions without reaching for `useState` + `fetch`. It integrates natively with the progressive enhancement model.

⚠️ **Gotcha:** Errors thrown in Server Actions bubble to the nearest `error.tsx` boundary in the tree — unless you return error state explicitly. For form validation errors, return structured data rather than throwing.

---

## Route Handlers, Middleware, and Edge Runtime

### Q: When do you use middleware vs. Route Handlers, and what does the edge runtime trade-off look like?

**Middleware** (`middleware.ts` at project root): Runs before every matched request. Use for auth redirects, A/B testing, geolocation, header injection. Must return quickly — it's on the hot path. Runs on the Edge runtime only.

```tsx
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(req: NextRequest) {
  const token = req.cookies.get('session')?.value;
  if (!token && req.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', req.url));
  }
  return NextResponse.next();
}

export const config = { matcher: ['/dashboard/:path*'] };
```

**Edge runtime:** V8 isolates with near-zero cold start. No Node.js APIs (no `fs`, no native modules, limited crypto). 1MB code size limit on Vercel. Perfect for middleware, auth checks, geo-routing.

**Node.js runtime:** Full Node.js environment. Use for Route Handlers that need database drivers, native modules, or large dependencies. Cold start is ~100-500ms on serverless.

```tsx
// app/api/products/route.ts
export const runtime = 'nodejs'; // explicit, or 'edge'

export async function GET(req: Request) {
  const products = await db.product.findMany();
  return Response.json(products);
}
```

> 💡 **Senior insight:** Middleware is stateless and can't call your database directly (no Node.js, no ORM). For auth, validate a JWT or lightweight session token at the edge; defer heavy DB lookups to the server component or route handler.

⚠️ **Gotcha:** Route Handlers in the App Router do not share the same caching as `fetch` in Server Components. A `GET /api/products` response is not automatically stored in the Data Cache — that cache only applies to `fetch()` calls made in Server Components.

---

## Navigation

### Q: How does Next.js prefetching work and what are the router navigation APIs?

`<Link>` automatically prefetches the linked page when it enters the viewport. In Next 14, this prefetched the full static segment. In Next 15, it only prefetches up to the first `loading.tsx` boundary — trading bundle size for faster link rendering.

```tsx
import Link from 'next/link';

// Disable prefetch for low-priority links
<Link href="/rarely-visited" prefetch={false}>Visit</Link>
```

**Programmatic navigation:**
```tsx
'use client';
import { useRouter } from 'next/navigation'; // not 'next/router' — App Router
import { redirect } from 'next/navigation';  // server-side redirect

export function LogoutButton() {
  const router = useRouter();
  return (
    <button onClick={() => {
      logout();
      router.push('/login');
      // router.refresh() — re-fetches server components, clears Router Cache
      // router.replace('/login') — no history entry
    }}>
      Logout
    </button>
  );
}
```

**`notFound()` and `redirect()`** can be called in Server Components — they throw special errors caught by the framework:
```tsx
import { notFound, redirect } from 'next/navigation';

async function ProductPage({ params }: { params: { id: string } }) {
  const product = await getProduct(params.id);
  if (!product) notFound(); // renders not-found.tsx
  if (!product.published) redirect('/coming-soon');
  return <ProductDetail product={product} />;
}
```

---

## Metadata API and SEO

### Q: How do you handle SEO and dynamic metadata in App Router?

**Static metadata:**
```tsx
// app/layout.tsx
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: { template: '%s | Acme Corp', default: 'Acme Corp' },
  description: 'The best product on earth',
  openGraph: { images: ['/og.png'] },
};
```

**Dynamic metadata:**
```tsx
// app/product/[id]/page.tsx
export async function generateMetadata({ params }: { params: { id: string } }): Promise<Metadata> {
  const product = await getProduct(params.id);
  return {
    title: product.name,
    description: product.description,
    openGraph: { images: [product.imageUrl] },
  };
}
```

**`generateStaticParams`:** Pre-generates static paths at build time for dynamic segments. Required for SSG of dynamic routes.
```tsx
export async function generateStaticParams() {
  const products = await getProducts();
  return products.map(p => ({ id: p.id }));
}
```

> 💡 **Senior insight:** `generateMetadata` runs on the server and shares the same fetch cache as the page. Next.js deduplicates the `getProduct` call via Request Memoization, so you pay zero extra network cost for the metadata fetch.

---

## Image, Font, and Script Optimization

### Q: What does Next.js do automatically for assets and why does it matter for Core Web Vitals?

**`next/image`:** Automatically serves modern formats (WebP/AVIF), resizes to the requested display size, lazy loads by default, and prevents Cumulative Layout Shift via required `width`/`height` or `fill`. LCP images should get `priority` to preload.

```tsx
import Image from 'next/image';

<Image
  src="/hero.jpg"
  alt="Hero banner"
  width={1200}
  height={600}
  priority        // preloads — use for above-fold images
  sizes="(max-width: 768px) 100vw, 50vw"
/>
```

**`next/font`:** Downloads Google Fonts at build time, self-hosts them, applies `font-display: optional` to eliminate layout shift. Zero client-side requests to Google.

```tsx
import { Inter } from 'next/font/google';
const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
```

**`next/script`:** Controls script loading strategy — `beforeInteractive`, `afterInteractive` (default), or `lazyOnload`. Prevents third-party scripts from blocking render.

---

## Auth Patterns in App Router

### Q: Where do you enforce authentication in App Router and how do `cookies()` and `headers()` work?

**Layered approach:**

1. **Middleware** — Edge-level redirect for unauthenticated requests (fast, but limited to lightweight token validation)
2. **Server Components** — Re-validate session before rendering sensitive data (defense in depth)
3. **Server Actions** — Always re-validate before mutations

```tsx
// lib/auth.ts — shared session helper
import { cookies } from 'next/headers';

export async function getSession() {
  const token = cookies().get('session')?.value;
  if (!token) return null;
  return validateJWT(token); // verify signature, check expiry
}
```

```tsx
// app/dashboard/page.tsx
import { getSession } from '@/lib/auth';
import { redirect } from 'next/navigation';

export default async function DashboardPage() {
  const session = await getSession();
  if (!session) redirect('/login');
  return <Dashboard user={session.user} />;
}
```

`cookies()` and `headers()` mark the route as dynamic (opt out of static rendering). Call them only where needed to preserve static rendering for public pages.

> 💡 **Senior insight:** Auth libraries like NextAuth v5 / Auth.js are built around this pattern — they expose a `auth()` helper for Server Components and middleware integration that shares a session check without double-fetching.

---

## Deployment Realities

### Q: What should a senior engineer know about deploying Next.js to production?

**Vercel (first-party):** Each route segment is automatically deployed as a serverless function (Node) or edge function. Static assets go to CDN. ISR is handled natively with shared cache across regions. Zero config; the trade-off is vendor lock-in and cost at scale.

**Self-host:** `next build && next start` runs a Node.js server. ISR requires a shared cache adapter (Redis) — without it, each pod has its own Data Cache and revalidation is inconsistent. Full Route Cache is per-instance by default.

**Cold starts:** Serverless Node.js functions have ~100-500ms cold starts. Edge functions start in ~5ms but can't use Node.js APIs. Bundle size directly affects cold start — tree-shake aggressively. Use `@next/bundle-analyzer` to profile.

**Key production checklist:**
- Set `output: 'standalone'` for Docker deployments (copies only necessary node_modules)
- Configure `NEXT_PUBLIC_` env vars for client-side access; never expose secrets with this prefix
- Use `next/headers` only in server context — crashes during static generation if misused

---

## Pages Router — Quick Contrast

### Q: Explain Pages Router data fetching for legacy codebases.

| Function | Runs when | Equivalent App Router pattern |
|---|---|---|
| `getStaticProps` | Build time | Static server component + `generateStaticParams` |
| `getStaticPaths` | Build time | `generateStaticParams` |
| `getServerSideProps` | Every request | Dynamic server component (reads cookies/headers) |
| `getInitialProps` | Server + client (bad) | Avoid; was an anti-pattern |

```tsx
// pages/product/[id].tsx (Pages Router)
export async function getServerSideProps({ params, req }) {
  const session = getSessionFromCookie(req);
  if (!session) return { redirect: { destination: '/login', permanent: false } };
  const product = await getProduct(params.id);
  return { props: { product } };
}
```

The Pages Router cannot incrementally stream — the entire `getServerSideProps` must resolve before any HTML is sent. This is the core UX argument for migrating to App Router.

> 💡 **Senior insight:** Incrementally migrate by running App Router (`app/`) and Pages Router (`pages/`) side by side — Next.js supports both in the same project. Migrate leaf routes first, shared layouts last.

---

## ⚡ Rapid-Fire

- **What does `"use client"` actually do?** Marks a module boundary. All code in the file and its imports run on the client. Server Components can still render as children via composition.
- **Can you `await` in a layout?** Yes — `layout.tsx` can be an async Server Component.
- **Difference between `redirect()` and `permanentRedirect()`?** 307 vs 308 HTTP status. Use permanent for SEO-friendly moves.
- **What is `unstable_cache`?** A way to cache arbitrary async functions (not just `fetch`) in the Data Cache.
- **How do you access search params in a Server Component?** Via the `searchParams` prop on `page.tsx` — it's a plain object, not a URL instance.
- **What breaks if you use `Math.random()` in a Server Component?** Static rendering will fail — it's non-deterministic. Use `export const dynamic = 'force-dynamic'`.
- **What is the `template.tsx` use case?** Remounting on navigation — entry animations, per-page analytics events, form state reset.
- **How do you share state between parallel routes?** URL state (search params) or a shared parent context via a Client Component layout.
- **Does `next/image` require a domain allowlist?** Yes — remote images must be configured in `next.config.ts` under `images.remotePatterns`.
- **What triggers dynamic rendering?** `cookies()`, `headers()`, `searchParams`, `fetch` with `no-store`, `Date.now()`, `Math.random()`.

---

## 🚩 Red Flags

- **Fetching data in Client Components with `useEffect`** when a Server Component could do it — inflates bundle, loses streaming, exposes round-trip latency.
- **Not revalidating after mutations** — calling a Server Action that writes to DB without `revalidateTag` / `revalidatePath` means users see stale data until the cache expires.
- **Assuming Next 14 caching defaults in Next 15** — forgetting that `fetch` is now `no-store` by default causes massive over-fetching and database hammering.
- **Putting auth checks only in middleware** — middleware is bypassed by direct API calls. Always re-validate session in Server Actions and Route Handlers.
- **Importing server-only code into Client Components** — secrets, DB clients, or `"server-only"` packages will error at runtime if accidentally bundled. Use the `server-only` package as a guard.
- **Using `useRouter` from `next/router` in App Router** — it's `next/navigation`. The error is confusing because both can resolve without compile errors.
- **Wrapping the entire app in `"use client"`** — defeats RSC entirely; usually done by devs who don't understand the boundary.
- **Not setting `sizes` on `next/image`** — the browser fetches a 1200px image for a 200px slot, destroying LCP.
- **Using `getInitialProps` in new code** — it was always an anti-pattern; runs on both server and client and prevents static optimisation.
- **Forgetting that `error.tsx` must be a Client Component** — the framework silently ignores a server component error boundary or throws a cryptic error.
