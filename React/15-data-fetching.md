# Data Fetching: Transports, Patterns, and Correctness

Data fetching in React is deceptively complex — the raw mechanics are simple, but production-grade correctness requires understanding race conditions, cancellation, caching layers, real-time transports, and failure modes. This guide focuses on the discipline of fetching itself: when to use what, what can go wrong, and how senior engineers think about the full lifecycle from request to render. For server-state philosophy and when to reach for TanStack Query, see **file 06 (state-management)**; for Next.js RSC/server fetching, see **file 08**.

---

## The Fetch API — Deeper Than You Think

### Q: What are the most important things to understand about the native Fetch API?

**Trade-off:** Fetch is powerful and sufficient for most use cases, but its defaults and error model surprise engineers who haven't read past the happy path.

**Error model — the classic gotcha:**

```ts
// ⚠️ This does NOT throw on 404 or 500
const res = await fetch('/api/users');
// res.ok is false, but no exception was thrown

// Correct pattern:
const res = await fetch('/api/users');
if (!res.ok) {
  throw new Error(`HTTP ${res.status}: ${res.statusText}`);
}
const data = await res.json();
```

Fetch only rejects the promise on **network failure** (DNS, connection refused, CORS abort). 4xx and 5xx are successful HTTP exchanges — you must check `res.ok` or `res.status` yourself.

**Credentials and CORS:**

```ts
// Include cookies for same-origin and cross-origin requests
fetch('/api/data', { credentials: 'include' });
// 'same-origin' (default) | 'include' | 'omit'
```

**Timeouts via AbortController:**

Fetch has no built-in timeout. Use `AbortController`:

```ts
async function fetchWithTimeout(url: string, ms = 5000): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), ms);
  try {
    const res = await fetch(url, { signal: controller.signal });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res;
  } finally {
    clearTimeout(id);
  }
}
```

**Streaming responses (React 18+):**

```ts
const res = await fetch('/api/stream');
const reader = res.body!.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  console.log(decoder.decode(value)); // chunk
}
```

> 💡 Senior insight: The `Response` object is a single-read stream — calling `.json()` and then `.text()` on the same response will fail. Clone it (`res.clone()`) if you need to read the body more than once or log raw responses for debugging.

**Follow-ups they'll ask:**
- How does `mode: 'cors'` differ from `mode: 'no-cors'`? (`no-cors` gives an opaque response — you cannot read headers or body.)
- Can you cancel a fetch mid-stream? (Yes — `controller.abort()` mid-read terminates the stream.)
- What is `keepalive: true` used for? (Lets the request outlive the page, useful for analytics on `visibilitychange`/`beforeunload`.)

---

## Axios vs Fetch

### Q: In 2024-25, does Axios still justify its place in a new project?

**Trade-off:** Axios provides ergonomic wins (interceptors, automatic JSON, instance config, built-in timeout) at the cost of a ~14 KB dependency. For modern projects already using a fetching library like TanStack Query, the overlap is significant.

**Where Axios still earns its keep:**

```ts
// Centralized auth + error interceptor — hard to replicate cleanly with fetch
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 10_000,
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  config.headers.Authorization = `Bearer ${getToken()}`;
  return config;
});

api.interceptors.response.use(
  (res) => res.data, // auto-unwrap
  async (error) => {
    if (error.response?.status === 401) await refreshToken();
    return Promise.reject(error);
  }
);
```

**Fetch equivalent (more boilerplate, but doable):**

```ts
// You end up building the same abstraction yourself
async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { Authorization: `Bearer ${getToken()}`, ...init?.headers },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}
```

**Decision matrix:**

| Need | Fetch | Axios |
|---|---|---|
| Automatic JSON parse | Manual `.json()` | Built-in |
| Request/response interceptors | Wrapper function | First-class |
| Upload progress | `ReadableStream` / XHR fallback | Built-in via XHR |
| Request cancellation | `AbortController` | `AbortController` (v1+) |
| Built-in timeout | No | Yes |
| Bundle size | 0 KB | ~14 KB |
| Node.js native (18+) | Yes | Yes |

> 💡 Senior insight: If you're already using TanStack Query with a custom `queryFn`, a thin `apiFetch` wrapper over native fetch is almost always sufficient. Axios shines in REST-heavy projects with complex auth flows, multi-tenant base URLs, or teams that want uniform error shapes without a fetching library.

⚠️ **Gotcha:** Axios throws on 4xx/5xx (correct behavior), but the error shape is `error.response.data`, not `error.message`. Teams switching from fetch to Axios mid-project often have mismatched error handling conventions.

---

## Fetching in React — The Right Way

### Q: What's wrong with a plain `useEffect` + `useState` fetch, and when is it acceptable?

**Trade-off:** The naive pattern works for throwaway demos but has at least six production-breaking problems. A library solves all of them; a careful `useEffect` can solve the most critical one (race conditions) but not the rest.

**The naive pattern and its problems:**

```ts
// ❌ Every problem listed below applies here
function UserProfile({ id }: { id: string }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/users/${id}`)
      .then(r => r.json())
      .then(setUser)
      .finally(() => setLoading(false));
  }, [id]);
  // ...
}
```

Problems:
1. **Race condition** — if `id` changes fast, an earlier response can arrive after a later one
2. **State-after-unmount** — `setUser` on an unmounted component (React 18 suppresses the warning but state is still set)
3. **No caching** — every mount refetches
4. **No deduplication** — two mounted instances issue two requests
5. **No retry** — transient failures silently fail
6. **Waterfall by default** — sequential `useEffect` chains kill performance

**Correct useEffect pattern (race + unmount fixed):**

```ts
function useUser(id: string) {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false; // ignore-flag pattern
    const controller = new AbortController();

    setLoading(true);
    fetch(`/api/users/${id}`, { signal: controller.signal })
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<User>;
      })
      .then(data => { if (!cancelled) setUser(data); })
      .catch(err => { if (!cancelled && err.name !== 'AbortError') setError(err); })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [id]);

  return { user, error, loading };
}
```

> 💡 Senior insight: The `ignore-flag` pattern and `AbortController` together handle both the logical race (stale response applied) and the network race (in-flight request cancelled). In a library like TanStack Query, both are handled internally — which is why using a library is the senior default for any production fetch.

**Follow-ups they'll ask:**
- Why use both `cancelled` flag and `abort`? (`abort` cancels the network request to save bandwidth; `cancelled` guards against state updates from synchronous or already-resolved promises that `abort` cannot stop.)
- When is bare `useEffect` acceptable? (One-off fire-and-forget side effects, imperative APIs like analytics, or inside a thin custom hook that you own end-to-end with no caching needs.)

---

## Request Lifecycle Concerns

### Q: What does a complete request lifecycle look like beyond happy-path loading?

**Trade-off:** Modeling loading/error/empty/success as four distinct states (not just a boolean `loading`) is a prerequisite for a good UX. Each has its own render path.

```ts
type FetchState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; error: Error }
  | { status: 'empty' }
  | { status: 'success'; data: T };
```

**Retries with exponential backoff:**

```ts
async function fetchWithRetry<T>(
  url: string,
  maxRetries = 3,
  baseDelay = 300
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch (err) {
      if (attempt === maxRetries) throw err;
      // Only retry on 5xx or network errors, not 4xx
      if (err instanceof Error && err.message.startsWith('HTTP 4')) throw err;
      await new Promise(r => setTimeout(r, baseDelay * 2 ** attempt));
    }
  }
  throw new Error('unreachable');
}
```

**Idempotency:** GET and DELETE are idempotent — safe to retry. POST is not; use an idempotency key header (`Idempotency-Key: <uuid>`) for POST retries to prevent duplicate side effects.

> 💡 Senior insight: Add jitter to exponential backoff (`delay * Math.random()`) to prevent thundering herd when many clients retry simultaneously after an outage.

---

## TanStack Query — Fetching Mechanics Deep Dive

### Q: Walk through TanStack Query's core fetching mechanics — not why to use it, but how it works.

**Trade-off:** TanStack Query's power comes from a deterministic cache keyed by structured query keys, with a clear staleness/garbage-collection model. Misunderstanding `staleTime` vs `gcTime` is the most common senior-level mistake.

**Query keys — structure matters:**

```ts
// Hierarchical keys enable targeted invalidation
const keys = {
  users: () => ['users'] as const,
  user: (id: string) => ['users', id] as const,
  userPosts: (id: string) => ['users', id, 'posts'] as const,
};

// Invalidate all user queries:
queryClient.invalidateQueries({ queryKey: keys.users() });
// Invalidate one user's posts only:
queryClient.invalidateQueries({ queryKey: keys.userPosts(userId) });
```

**`staleTime` vs `gcTime`:**

```ts
useQuery({
  queryKey: keys.user(id),
  queryFn: () => fetchUser(id),
  staleTime: 5 * 60 * 1000,  // Don't refetch if data is < 5 min old
  gcTime: 10 * 60 * 1000,    // Remove from cache 10 min after last subscriber
});
```

- `staleTime`: How long cached data is considered fresh (no background refetch). Default: `0`.
- `gcTime` (formerly `cacheTime`): How long inactive (unsubscribed) cache entries live before garbage collection. Default: `5min`.

**Refetch triggers:**

```ts
useQuery({
  queryKey: ['data'],
  queryFn: fetchData,
  refetchOnWindowFocus: true,    // default true — refetch when tab regains focus
  refetchOnReconnect: true,      // default true — refetch after network reconnect
  refetchInterval: 30_000,       // polling every 30s (falsy = off)
  refetchIntervalInBackground: false,
});
```

**Optimistic updates with rollback:**

```ts
const mutation = useMutation({
  mutationFn: (updated: User) => api.put(`/users/${updated.id}`, updated),
  onMutate: async (updated) => {
    await queryClient.cancelQueries({ queryKey: keys.user(updated.id) });
    const previous = queryClient.getQueryData<User>(keys.user(updated.id));
    queryClient.setQueryData(keys.user(updated.id), updated); // optimistic
    return { previous }; // context for rollback
  },
  onError: (_err, updated, context) => {
    queryClient.setQueryData(keys.user(updated.id), context?.previous); // rollback
  },
  onSettled: (_data, _err, updated) => {
    queryClient.invalidateQueries({ queryKey: keys.user(updated.id) });
  },
});
```

**Infinite queries (cursor-based):**

```ts
const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
  queryKey: ['posts'],
  queryFn: ({ pageParam }) => fetchPosts({ cursor: pageParam }),
  initialPageParam: undefined as string | undefined,
  getNextPageParam: (lastPage) => lastPage.nextCursor ?? undefined,
});
// data.pages is an array of page results — flatten for rendering
```

**Prefetching on hover/intent:**

```ts
function UserLink({ id }: { id: string }) {
  const queryClient = useQueryClient();
  return (
    <a
      href={`/users/${id}`}
      onMouseEnter={() =>
        queryClient.prefetchQuery({
          queryKey: keys.user(id),
          queryFn: () => fetchUser(id),
          staleTime: 60_000,
        })
      }
    >
      View profile
    </a>
  );
}
```

> 💡 Senior insight: Setting `staleTime: Infinity` for reference data (currencies, countries, config) means it loads once per session and never triggers a background refetch, significantly reducing server load in data-heavy apps.

**Follow-ups they'll ask:**
- What's the difference between `invalidateQueries` and `refetchQueries`? (`invalidate` marks stale and triggers background refetch only for active queries; `refetch` forces immediate refetch regardless of staleness.)
- How does TanStack Query deduplicate requests? (Multiple components with the same key share one in-flight request via an internal observer count.)
- See **file 06** for when-to-use TanStack Query philosophy vs local state.

---

## SWR

### Q: When is SWR a better choice than TanStack Query?

**Trade-off:** SWR is simpler, lighter (~4 KB vs ~13 KB), and sufficient for most read-heavy apps. TanStack Query wins on mutations, infinite queries, fine-grained cache control, and ecosystem.

```ts
import useSWR from 'swr';

const fetcher = (url: string) =>
  fetch(url).then(r => { if (!r.ok) throw new Error('fetch failed'); return r.json(); });

function Profile() {
  const { data, error, isLoading } = useSWR<User>('/api/user', fetcher, {
    revalidateOnFocus: true,
    dedupingInterval: 2000,
    errorRetryCount: 3,
  });
  // ...
}
```

The stale-while-revalidate HTTP pattern: serve cached (stale) data immediately, revalidate in the background, update when fresh data arrives. SWR makes this the default behavior.

**Choose SWR when:** mostly GET-heavy, simple invalidation, smaller bundle budget, or Next.js projects (same maintainer, first-class integration).
**Choose TanStack Query when:** complex mutations, optimistic updates, cursor pagination, offline support, or non-React frameworks.

---

## GraphQL, REST, and tRPC

### Q: How does the fetching model change between REST, GraphQL, and tRPC?

**Trade-off:** The transport choice fundamentally changes where N+1 problems live, how caching works, and what tooling is appropriate.

**GraphQL (Apollo/urql):** Normalized cache by `__typename + id` — the same object fetched in two queries is automatically merged. Apollo Client and urql both support Suspense, optimistic UI, and subscriptions. The trade-off: normalized cache invalidation is complex; overfetching is solved but underfetching/N+1 shifts to the resolver layer.

```ts
// Apollo — query deduplication and normalized cache built-in
const { data, loading } = useQuery(GET_USER, {
  variables: { id },
  fetchPolicy: 'cache-and-network', // show cache, revalidate in background
});
```

**tRPC:** End-to-end type safety with no codegen — the API contract is the TypeScript type. Built on TanStack Query under the hood, so all TQ mechanics apply. Best for full-stack TypeScript monorepos.

```ts
// tRPC + TanStack Query — fully typed, no schema
const { data } = trpc.user.byId.useQuery({ id });
```

**REST vs GraphQL vs tRPC:**

| Concern | REST | GraphQL | tRPC |
|---|---|---|---|
| Type safety | Manual/codegen | Codegen | Native TS |
| Overfetch | Common | Solved | Solved |
| Caching | HTTP cache friendly | Custom normalized | TanStack Query |
| Real-time | SSE/WS bolt-on | Subscriptions | WS/SSE bolt-on |
| Team fit | Any | Larger orgs | Full-stack TS |

---

## Real-Time Transports

### Q: When do you choose polling vs WebSockets vs Server-Sent Events?

**Trade-off:** Each transport has a different complexity-to-capability ratio. Start with the simplest that meets your latency and directionality requirements.

**Short polling:** Simple, works everywhere, high server load at scale.

```ts
// TanStack Query makes polling trivial
useQuery({ queryKey: ['status'], queryFn: fetchStatus, refetchInterval: 5000 });
```

**Long polling:** Server holds the request open until data is available, then client immediately reconnects. Lower overhead than short polling, higher than SSE/WS.

**Server-Sent Events (SSE):** Unidirectional server→client, HTTP/1.1 compatible, automatic browser reconnection, ideal for notifications/feeds.

```ts
useEffect(() => {
  const es = new EventSource('/api/events', { withCredentials: true });
  es.addEventListener('update', (e) => {
    queryClient.setQueryData(['feed'], JSON.parse(e.data));
  });
  es.onerror = () => es.close(); // let EventSource auto-reconnect
  return () => es.close();
}, []);
```

**WebSockets:** Bidirectional, lower latency, more complex lifecycle (connection management, reconnection, backpressure, auth).

```ts
function useLiveData(url: string) {
  const [data, setData] = useState(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    ws.onmessage = (e) => setData(JSON.parse(e.data));
    ws.onclose = () => { /* reconnect with backoff */ };
    return () => ws.close();
  }, [url]);

  return data;
}
```

**Integrating sockets with TanStack Query cache:**

```ts
useEffect(() => {
  const ws = new WebSocket('/ws/users');
  ws.onmessage = (e) => {
    const user: User = JSON.parse(e.data);
    // Inject real-time updates directly into the cache
    queryClient.setQueryData(keys.user(user.id), user);
  };
  return () => ws.close();
}, [queryClient]);
```

**`useSyncExternalStore` for external subscriptions (React 18+):**

```ts
function useSocketStore<T>(subscribe: (cb: () => void) => () => void, getSnapshot: () => T) {
  return useSyncExternalStore(subscribe, getSnapshot);
}
```

**Transport decision matrix:**

| Transport | Direction | Latency | Reconnect | Best for |
|---|---|---|---|---|
| Short poll | Client pull | Seconds | N/A | Dashboards, low-freq updates |
| Long poll | Client pull | ~100ms | Manual | Chat, queues |
| SSE | Server push | ~50ms | Automatic | Notifications, live feeds |
| WebSocket | Bidirectional | ~10ms | Manual | Chat, gaming, collaboration |

> 💡 Senior insight: SSE is underused. For 90% of "real-time" requirements (notifications, live counters, feed updates), SSE gives you lower complexity than WebSockets, free HTTP load balancer compatibility, and automatic browser reconnection. Reserve WebSockets for true bidirectionality.

⚠️ **Gotcha:** WebSocket connections don't send cookies by default in all browsers. Auth must be handled via token in the URL or a handshake message, not session cookies.

**Follow-ups they'll ask:**
- What is backpressure and how do you handle it with WebSockets? (Producer outpaces consumer; handle with a bounded buffer/queue or `pause()`/`resume()` on Node streams.)
- How do you handle WebSocket reconnection? (Exponential backoff with jitter; track `reconnectAttempts`; re-subscribe to channels after reconnect.)

---

## Suspense for Data Fetching

### Q: How does Suspense fit into data fetching in React 18/19?

**Trade-off:** Suspense enables render-as-you-fetch (the correct model) but requires libraries or the new `use()` hook to integrate — you cannot use it with bare `useEffect`.

**Three models:**

- **Fetch-on-render** (old): Component renders → useEffect fires → shows spinner → re-renders with data. Creates waterfalls.
- **Fetch-then-render**: Fetch all data before rendering. No waterfall but no progressive loading.
- **Render-as-you-fetch**: Start fetching before rendering, Suspense shows fallback until ready. Best UX.

**React 19 `use()` hook:**

```tsx
// use() integrates a promise into the Suspense/ErrorBoundary system
import { use, Suspense } from 'react';

function UserName({ userPromise }: { userPromise: Promise<User> }) {
  const user = use(userPromise); // suspends until resolved
  return <span>{user.name}</span>;
}

// Parent initiates fetch before rendering child
function Page({ id }: { id: string }) {
  const userPromise = fetchUser(id); // start fetch immediately
  return (
    <Suspense fallback={<Skeleton />}>
      <ErrorBoundary fallback={<Error />}>
        <UserName userPromise={userPromise} />
      </ErrorBoundary>
    </Suspense>
  );
}
```

**TanStack Query + Suspense:**

```tsx
const { data } = useSuspenseQuery({
  queryKey: keys.user(id),
  queryFn: () => fetchUser(id),
});
// No loading/error state needed — Suspense and ErrorBoundary handle it
```

> 💡 Senior insight: `useSuspenseQuery` is strictly better than `useQuery` when you have a Suspense boundary — it narrows the return type to `{ data: T }` (never undefined), eliminating null checks. It also enables automatic parallel data loading when multiple `useSuspenseQuery` calls exist in sibling components under a shared boundary.

---

## Error Handling Architecture

### Q: How should error handling be architected across a data-heavy app?

**Trade-off:** Per-component error states work for isolated failures; Error Boundaries provide a declarative safety net for unexpected errors; a combined strategy gives both granularity and safety.

```tsx
// Global error boundary catches unexpected errors + query errors in Suspense mode
<QueryErrorResetBoundary>
  {({ reset }) => (
    <ErrorBoundary onReset={reset} fallbackRender={({ resetErrorBoundary }) => (
      <div>
        <p>Something went wrong.</p>
        <button onClick={resetErrorBoundary}>Retry</button>
      </div>
    )}>
      <Suspense fallback={<Spinner />}>
        <DataHeavyPage />
      </Suspense>
    </ErrorBoundary>
  )}
</QueryErrorResetBoundary>
```

**TanStack Query retry policy:**

```ts
useQuery({
  queryKey: ['data'],
  queryFn: fetchData,
  retry: (failureCount, error) => {
    // Don't retry 4xx (client errors), do retry 5xx up to 3 times
    if (error instanceof HttpError && error.status < 500) return false;
    return failureCount < 3;
  },
  retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30_000),
});
```

**Offline handling:** TanStack Query v5 supports `networkMode: 'offlineFirst'` — queries are paused (not failed) when offline and automatically resume on reconnect.

---

## Performance: Waterfalls, Parallel Fetching, and Caching

### Q: How do you eliminate request waterfalls and maximize fetching performance?

**Trade-off:** Sequential fetches are the default but are almost always wrong. Parallelism and prefetching can cut perceived load time dramatically.

**Waterfall (bad):**

```ts
// Each awaits the previous — if each takes 300ms, total is 900ms+
const user = await fetchUser(id);
const posts = await fetchUserPosts(user.id);
const comments = await fetchPostComments(posts[0].id);
```

**Parallel (correct when independent):**

```ts
// All fire simultaneously — total time is the slowest, not the sum
const [user, settings, notifications] = await Promise.all([
  fetchUser(id),
  fetchSettings(id),
  fetchNotifications(id),
]);
```

**TanStack Query parallel queries:**

```ts
// useQueries fires all in parallel and deduplicates
const results = useQueries({
  queries: userIds.map(id => ({
    queryKey: keys.user(id),
    queryFn: () => fetchUser(id),
  })),
});
```

**Prefetch on route transition:**

```ts
// React Router loader — prefetch before component mounts
export async function loader({ params }: LoaderFunctionArgs) {
  await queryClient.prefetchQuery({
    queryKey: keys.user(params.id!),
    queryFn: () => fetchUser(params.id!),
  });
  return null;
}
```

**Request batching:** If your API supports it, batch multiple IDs into one request (`/api/users?ids=1,2,3`) rather than N individual requests. Libraries like `dataloader` automate batching.

> 💡 Senior insight: The most impactful performance fix is usually prefetching on user intent (hover, focus, route prediction) — data that arrives before the user needs it has zero perceived latency. See **file 07** for broader caching layer strategy.

**Follow-ups they'll ask:**
- What is the difference between parallel queries and dependent queries? (Dependent queries use `enabled: !!prerequisiteData` to conditionally fire after a dependency resolves.)
- How do you avoid re-fetching on every navigation? (Appropriate `staleTime` — e.g. `staleTime: 60_000` means if the user navigates away and back within 60s, no refetch occurs.)

---

## ⚡ Rapid-Fire

**Q: Fetch rejects on network error or HTTP error?**
Network error only. Check `res.ok` for HTTP errors.

**Q: `staleTime: 0` means what?**
Data is immediately stale — TanStack Query will background-refetch on every mount and focus. Default behavior.

**Q: What's the ignore-flag pattern?**
A `let cancelled = false` variable in `useEffect` that prevents state updates from stale async callbacks after cleanup runs.

**Q: SSE vs WebSocket for a notification feed?**
SSE — unidirectional, simpler, automatic reconnect, HTTP compatible.

**Q: How do you prevent a mutation from running twice on double-click?**
`mutation.isPending` — disable the button while a mutation is in flight.

**Q: What is `gcTime: 0`?**
Cache entries are removed immediately when all subscribers unmount — effectively disables caching.

**Q: When should you use `queryClient.setQueryData` directly?**
After a successful mutation when you already have the updated server response — avoids a redundant refetch.

**Q: What HTTP method should retries be careful with?**
POST — not idempotent. Use idempotency keys or only retry on network errors, not on response errors.

**Q: Render-as-you-fetch requires what?**
A Suspense boundary and either `use()` (React 19), `useSuspenseQuery`, or a Suspense-compatible library.

**Q: How do you share a single WebSocket across components?**
Via a singleton (module-level or context), not per-component `useEffect`. Feed updates through `useSyncExternalStore`.

---

## 🚩 Red Flags

- Calling `fetch` with no `.ok` check and treating all responses as success
- Forgetting the `useEffect` cleanup — no `AbortController`, no ignore flag — in any hook that hits a changing dependency
- Using `loading: boolean` instead of four distinct states — empty and error are invisible
- Treating `staleTime` and `gcTime` as interchangeable
- Creating a new `AbortController` inside a `useCallback` with no dependency array — the signal is never used for cancellation
- Retrying POST requests without idempotency keys
- Choosing WebSockets for unidirectional server-push when SSE would suffice
- Fetching sequentially with `await` inside `useEffect` for independent resources (waterfall)
- Throwing away TanStack Query's optimistic update rollback mechanism and doing full refetches on mutation success
- Storing raw fetch responses (the `Response` object) in state — the body can only be read once
