# 06 — State Management

State management is one of the most consequential architectural decisions in a React application. Senior engineers are distinguished not by knowing every library's API, but by correctly classifying state first and then selecting the minimal, appropriate tool — avoiding the endemic mistake of treating every piece of state as global client state.

---

## The First Principle: Classify Your State

Before reaching for any library, ask what *kind* of state you have. Most "state management pain" is a misclassification problem.

| Category | Definition | Right Tool |
|---|---|---|
| **Server / cache state** | Data owned by the server; you hold a local copy | TanStack Query, SWR |
| **Client UI state** | Ephemeral interaction state: modals, tooltips, tabs | `useState`, `useReducer` |
| **Shared client state** | True app-wide UI state: auth session, theme, feature flags | Context, Zustand, Redux |
| **URL state** | Filters, pagination, selected IDs — survives refresh, supports deep-link | `searchParams`, `nuqs` |
| **Form state** | In-flight user input before submission | react-hook-form |
| **Ephemeral / transient** | Animation values, drag position — never needs to hit React | `useRef`, Zustand transient |

> 💡 Senior insight: In most apps, 60–70 % of what lives in a Redux store is actually server state. Migrating it to TanStack Query typically cuts store complexity by half and eliminates an entire class of bugs (stale data, loading flags, error flags, refetch logic).

---

## Decision Framework: Which Tool When

Work through this sequence before writing any state code.

**1. Is the data fetched from a server?**
Use TanStack Query (or SWR). Do not put it in Redux, Context, or Zustand unless you have a documented reason (offline-first, cross-tab sync, etc.).

**2. Is it local to a single component or a small, co-located subtree?**
Use `useState` or `useReducer` inside the component. Lift only when a sibling actually needs it.

**3. Does it need to be shared across many components that are not in the same subtree?**
- Low-frequency updates (theme, locale, auth identity): Context API.
- High-frequency updates, or you need subscriptions, devtools, or persistence: Zustand.
- Large team, complex async flows, strong need for middleware/time-travel: Redux Toolkit.

**4. Does the value belong in the URL?**
Filters, sort order, selected entity IDs — if a user should be able to share the link or use the back button, the URL is the right store.

**5. Is it form input?**
React Hook Form with uncontrolled fields. Do not mirror form values into useState on every keystroke.

> 💡 Senior insight: The framework above is the answer to "how do you decide on state management?" in any senior interview. Walk the interviewer through the classification before mentioning any library name.

---

## Context API

### Q: What is Context actually good for, and what is it not?

**Trade-off:** Context is a *dependency injection* mechanism, not a state manager. It solves prop-drilling for low-frequency, stable values. It does not have subscriptions; every consumer re-renders when the context value reference changes.

**Good uses:**
- Theme (light/dark)
- Current authenticated user identity
- Locale / i18n configuration
- Feature flag set (fetched once on boot)
- Design-system component configuration (e.g., `size` default)

**Bad uses:**
- Anything that changes on user interaction (selected item, filter state)
- Server data cache
- Any state that many leaf components subscribe to independently

```tsx
// Splitting contexts prevents unrelated consumers from re-rendering
const ThemeContext = createContext<Theme>("light");
const AuthContext = createContext<AuthUser | null>(null);

// Memoize the value so identity is stable across parent re-renders
function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);

  // Stable reference: only changes when user actually changes
  const value = useMemo(() => ({ user, setUser }), [user]);

  return <AuthContext value={value}>{children}</AuthContext>;
}
```

⚠️ Gotcha: Placing a plain object literal `value={{ user }}` directly in JSX creates a new reference on every parent render, causing all consumers to re-render even when `user` has not changed. Always memoize.

⚠️ Gotcha: "Context selectors" (`use-context-selector`) exist but add complexity. If you find yourself needing them, your state is updating too frequently for Context — move to Zustand.

**Follow-ups they'll ask:**
- How does React 19's `use(Context)` differ from `useContext`? (Can be called conditionally; compatible with Suspense.)
- How do you prevent Context consumers from re-rendering when an unrelated slice of the value changes? (Split contexts, or use a store.)

---

## Redux Toolkit

### Q: When does Redux Toolkit still make sense in 2025?

**Trade-off:** RTK is the correct choice when you need: a large shared team working on a predictable state graph, complex async orchestration with middleware, time-travel debugging, or an established codebase that already uses Redux. It is overkill for apps where server state is handled by TanStack Query and UI state fits in Zustand.

```ts
// slices/cartSlice.ts
import { createSlice, createEntityAdapter, PayloadAction } from "@reduxjs/toolkit";
import type { CartItem } from "@/types";

const adapter = createEntityAdapter<CartItem>();

const cartSlice = createSlice({
  name: "cart",
  initialState: adapter.getInitialState({ status: "idle" as const }),
  reducers: {
    itemAdded: adapter.addOne,
    itemRemoved: adapter.removeOne,
    quantityUpdated(state, action: PayloadAction<{ id: string; qty: number }>) {
      // Immer allows this "mutation" — it produces a new immutable state
      const item = state.entities[action.payload.id];
      if (item) item.quantity = action.payload.qty;
    },
  },
});

export const { itemAdded, itemRemoved, quantityUpdated } = cartSlice.actions;
export const cartSelectors = adapter.getSelectors(
  (state: RootState) => state.cart
);
```

```ts
// Memoized selector with Reselect (bundled in RTK)
import { createSelector } from "@reduxjs/toolkit";

const selectCartTotal = createSelector(
  cartSelectors.selectAll,
  (items) => items.reduce((sum, i) => sum + i.price * i.quantity, 0)
);
// selectCartTotal is only recomputed when the items array reference changes
```

**RTK Query** (server state inside Redux):

```ts
const api = createApi({
  reducerPath: "api",
  baseQuery: fetchBaseQuery({ baseUrl: "/api" }),
  endpoints: (build) => ({
    getProducts: build.query<Product[], void>({
      query: () => "/products",
      providesTags: ["Product"],
    }),
    createProduct: build.mutation<Product, Partial<Product>>({
      query: (body) => ({ url: "/products", method: "POST", body }),
      invalidatesTags: ["Product"],
    }),
  }),
});
```

> 💡 Senior insight: RTK Query and TanStack Query solve the same problem. If you are already on Redux, RTK Query is the natural choice. If you are greenfield, TanStack Query has a lighter footprint and works without Redux.

**Follow-ups they'll ask:**
- What does Immer do and when would it cause a bug? (It uses Proxy objects; returning a new value AND mutating `state` in the same reducer causes an error.)
- How does `createEntityAdapter` normalize data and why does normalization matter? (Avoids O(n) lookups; prevents redundant entity copies.)
- What is middleware used for? (Logging, analytics, RTK Query's cache management, thunk execution.)

---

## Zustand

### Q: Why would you choose Zustand over Redux Toolkit for a mid-size app?

**Trade-off:** Zustand eliminates the boilerplate of actions/reducers/selectors while still providing a reactive, subscription-based store outside of React's Context tree. It scales well from a single store to a slices pattern. The main cost is weaker DevTools compared to Redux and no built-in entity normalization.

```ts
// store/useCartStore.ts
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
}

interface CartStore {
  items: Record<string, CartItem>;
  addItem: (item: CartItem) => void;
  removeItem: (id: string) => void;
  total: () => number;
}

export const useCartStore = create<CartStore>()(
  persist(
    immer((set, get) => ({
      items: {},
      addItem: (item) =>
        set((state) => {
          state.items[item.id] = item;
        }),
      removeItem: (id) =>
        set((state) => {
          delete state.items[id];
        }),
      total: () =>
        Object.values(get().items).reduce(
          (sum, i) => sum + i.price * i.quantity,
          0
        ),
    })),
    { name: "cart-storage" } // persists to localStorage
  )
);
```

**Selective subscriptions to prevent unnecessary re-renders:**

```tsx
import { useShallow } from "zustand/react/shallow";

// Only re-renders when `items` changes — not on total() calls
const items = useCartStore(useShallow((s) => s.items));

// Transient update pattern: read without subscribing (e.g., in event handlers)
const getTotal = useCartStore.getState;
```

**Slices pattern for large stores:**

```ts
// Each slice is a plain function; compose them in create()
const createAuthSlice = (set) => ({
  user: null as AuthUser | null,
  login: (u: AuthUser) => set({ user: u }),
  logout: () => set({ user: null }),
});
```

> 💡 Senior insight: Zustand's `getState()` lets you read store state inside callbacks, event handlers, and non-React code without subscribing. This is the correct pattern for analytics, websocket handlers, and imperative integrations.

⚠️ Gotcha: Without `useShallow`, passing a selector that returns an object literal causes a re-render on every state change. Always destructure primitives or use `useShallow` for object selectors.

**Follow-ups they'll ask:**
- How does Zustand avoid Context re-render issues? (The store lives outside React; components subscribe via a module-level event emitter, not Context.)
- How do you test a Zustand store? (Import the store, call actions directly, assert on `getState()`. No Provider needed.)

---

## Atomic State: Jotai and Recoil

### Q: When does the atomic model outperform a top-down store?

**Trade-off:** Atoms are individually subscribable units. A component that reads atom A does not re-render when atom B changes. This makes the model highly efficient for independent, fine-grained state across a large component tree — think spreadsheet cells, canvas objects, or per-row editor state. The cost is that cross-atom orchestration (transactions across many atoms) is harder to reason about than a single reducer.

```ts
// Jotai: atoms and derived atoms
import { atom, useAtom, useAtomValue } from "jotai";

const countAtom = atom(0);
const doubledAtom = atom((get) => get(countAtom) * 2); // derived, read-only

function Counter() {
  const [count, setCount] = useAtom(countAtom);
  const doubled = useAtomValue(doubledAtom);
  return <button onClick={() => setCount((c) => c + 1)}>{count} / {doubled}</button>;
}
```

> 💡 Senior insight: Jotai is an excellent fit when state is naturally *per-entity* (e.g., per-row in a data grid) and you want React Suspense integration with zero boilerplate. For most CRUD apps with a backend, TanStack Query covers more ground with less setup.

**Brief Recoil note:** Recoil introduced the atomic model to the React ecosystem but has seen slower maintenance since 2023. Jotai is the actively-maintained successor for teams wanting this model.

---

## TanStack Query (React Query)

### Q: How does TanStack Query change the architecture of a React application?

**Trade-off:** TanStack Query owns the entire async data lifecycle — fetching, caching, background refresh, deduplication, and error states. It eliminates the need to store server data in Redux or Zustand, cutting most apps' global state needs dramatically. The trade-off is that it is opinionated about data ownership: the cache, not your components, is the source of truth for server data.

```tsx
// Basic query
const { data: products, isLoading, error } = useQuery({
  queryKey: ["products", { category }],
  queryFn: () => fetchProducts(category),
  staleTime: 5 * 60 * 1000,  // data is fresh for 5 min; no refetch on mount
  gcTime: 10 * 60 * 1000,    // cache entry removed after 10 min of no subscribers
});
```

**staleTime vs gcTime:**
- `staleTime`: how long the cached data is considered fresh. During this window, no background refetch occurs.
- `gcTime` (formerly `cacheTime`): how long inactive cache entries survive before garbage collection.

**Mutation with optimistic update and rollback:**

```tsx
const queryClient = useQueryClient();

const mutation = useMutation({
  mutationFn: (updated: Product) => api.put(`/products/${updated.id}`, updated),
  onMutate: async (updated) => {
    // Cancel any in-flight refetches for this key
    await queryClient.cancelQueries({ queryKey: ["products", updated.id] });

    // Snapshot previous value for rollback
    const previous = queryClient.getQueryData<Product>(["products", updated.id]);

    // Optimistically update the cache
    queryClient.setQueryData(["products", updated.id], updated);

    return { previous };
  },
  onError: (_err, _updated, context) => {
    // Roll back to snapshot on error
    queryClient.setQueryData(["products", context!.previous!.id], context!.previous);
  },
  onSettled: (data) => {
    // Always refetch to sync with server truth
    queryClient.invalidateQueries({ queryKey: ["products", data!.id] });
  },
});
```

**Cache invalidation patterns:**

```ts
// Invalidate a specific entity
queryClient.invalidateQueries({ queryKey: ["products", id] });

// Invalidate an entire collection
queryClient.invalidateQueries({ queryKey: ["products"] });

// Prefetch on hover (perceived performance)
queryClient.prefetchQuery({ queryKey: ["products", id], queryFn: () => fetchProduct(id) });
```

> 💡 Senior insight: The `queryKey` is the cache key AND the dependency array. Treat it like a URL: it must fully describe the request. Including filters, pagination, and sort order in the key ensures correct cache isolation.

**SWR comparison:** SWR (Vercel) is lighter and excellent for simple data fetching. TanStack Query wins for complex invalidation graphs, mutations with optimistic UI, pagination, infinite scroll, and offline support.

⚠️ Gotcha: Setting `staleTime: Infinity` with no invalidation strategy means users see stale data forever. Always pair long `staleTime` values with explicit mutation-triggered invalidation.

**Follow-ups they'll ask:**
- How do you handle dependent queries? (`enabled: !!userId` — the query only runs when its dependency is available.)
- How do you share data between two components without re-fetching? (Same `queryKey` — the cache deduplicates the request.)
- How do you implement infinite scroll? (`useInfiniteQuery` with `getNextPageParam`.)

---

## URL as State

### Q: When should a value live in the URL instead of component state?

**Trade-off:** URL state is universally shareable, survives page refresh, and integrates with browser history for free. The cost is that URL updates cause a navigation (or history push), which can trigger re-renders across layout boundaries if not handled carefully.

Candidates for URL state: search query, filters, sort column/direction, pagination page, selected tab, selected entity ID in a master-detail layout.

```tsx
// Next.js App Router — reading and updating searchParams
"use client";
import { useSearchParams, useRouter, usePathname } from "next/navigation";

function FilterBar() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const setFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set(key, value);
    router.push(`${pathname}?${params.toString()}`);
  };

  return (
    <select onChange={(e) => setFilter("category", e.target.value)}
            value={searchParams.get("category") ?? "all"}>
      <option value="all">All</option>
      <option value="books">Books</option>
    </select>
  );
}
```

**nuqs** (`nuqs` package) provides a `useState`-like API over `searchParams`, handles serialization/deserialization, and batches updates:

```ts
import { parseAsInteger, useQueryState } from "nuqs";

const [page, setPage] = useQueryState("page", parseAsInteger.withDefault(1));
```

> 💡 Senior insight: In Next.js App Router, `searchParams` in Server Components make filter-driven pages fully server-rendered with no client state at all. The URL IS the state; the component just reads it.

---

## Form State

### Q: Why do uncontrolled forms scale better than controlled forms?

The answer lives in the forms-focused file (03), but the state management principle is: form input is ephemeral state that should not be mirrored into React state on every keystroke. React Hook Form registers inputs with the DOM directly, reads values on submit, and only triggers React re-renders for validation errors. This cuts re-renders from O(keystrokes) to O(validation events).

For global form state (e.g., a multi-step wizard), use React Hook Form's `useFormContext` rather than lifting controlled state into Zustand or Context.

---

## Comparison Table

| Dimension | Context API | Redux Toolkit | Zustand | Jotai | TanStack Query |
|---|---|---|---|---|---|
| **Primary use-case** | Stable config / DI | Complex shared client state | Shared UI state | Atomic, fine-grained state | Server / async cache state |
| **Re-render model** | All consumers on value change | Selector subscriptions | Per-selector subscriptions | Per-atom subscriptions | Per-query subscriptions |
| **Boilerplate** | Low | High | Very low | Low | Low |
| **Async support** | Manual | createAsyncThunk / RTK Query | Manual (or middleware) | Async atoms | First-class |
| **DevTools** | React DevTools | Redux DevTools (excellent) | Zustand DevTools (basic) | Jotai DevTools | TanStack Query DevTools |
| **Bundle size** | 0 (built-in) | ~12 kB | ~1 kB | ~3 kB | ~13 kB |
| **Persistence** | Manual | Redux Persist | `persist` middleware | `atomWithStorage` | N/A (server source of truth) |

---

## Common Architecture Mistakes

### Q: What are the most common state management anti-patterns you've seen in production?

**1. Global-everything**: Every piece of state is put in a Redux store "just in case." This creates unnecessary coupling, makes testing harder, and causes performance problems. State should live as close to where it is used as possible.

**2. Duplicating server data into Redux**:
```ts
// Anti-pattern: fetching then storing in Redux
dispatch(setProducts(await fetchProducts())); // now you own staleness

// Correct: TanStack Query owns the lifecycle
const { data } = useQuery({ queryKey: ["products"], queryFn: fetchProducts });
```

**3. Storing derived state instead of computing it**:
```ts
// Anti-pattern: storing a value that can be computed
const [isCartEmpty, setIsCartEmpty] = useState(cart.length === 0);

// Correct: derive it
const isCartEmpty = cart.length === 0; // no state, no sync bugs
```

**4. Prop-drilling vs. over-globalizing**: Teams oscillate between threading props five levels deep and putting everything in global state. The right answer is co-location first, then lifting to the nearest common ancestor, then Context or a store only when the ancestor is too far.

**5. Missing cache invalidation after mutations**: Updating an entity via mutation but forgetting to `invalidateQueries` means the list view shows stale data. Always pair mutations with invalidation or an optimistic update.

**6. Storing derived/computed values in URL**: The URL should store *inputs* (filters, IDs), not *outputs* (computed totals, formatted labels). Recompute outputs from inputs in the component or server.

> 💡 Senior insight: In a code review, the fastest way to identify state management debt is to look for: loading flags (`isLoading`, `isFetching`) in a Redux store (server state), `useEffect` that syncs one piece of state into another (derived state stored), and Context providers wrapping the entire app tree for frequently-changing values.

---

## ⚡ Rapid-Fire

**Q: What is the difference between `staleTime` and `gcTime` in TanStack Query?**
`staleTime` controls when data is considered outdated and eligible for background refetch. `gcTime` controls when the inactive cache entry is deleted from memory.

**Q: Why is Context not a state manager?**
Context is a transport mechanism. It has no built-in subscriptions — consumers re-render on every value change regardless of whether they use the changed slice.

**Q: What makes a Zustand selector cause unnecessary re-renders?**
Returning a new object reference from the selector on every call. Use `useShallow` or select primitive values.

**Q: When would you pick Jotai over Zustand?**
When state is naturally per-entity and independent (e.g., per-row in a table), or when you want first-class Suspense integration at the atom level.

**Q: Can you use TanStack Query and Zustand together?**
Yes. TanStack Query handles server state; Zustand handles client UI state that is not tied to a server resource. They complement each other cleanly.

**Q: What is `createEntityAdapter` in RTK?**
A utility that generates a normalized `{ ids: [], entities: {} }` structure and pre-built CRUD reducers (add, update, remove, upsert) plus selectors, eliminating O(n) array scans.

**Q: How do you persist Zustand state across page reloads?**
The `persist` middleware wraps the store and syncs it to `localStorage` (or any custom storage adapter) automatically.

**Q: What is the `enabled` option in `useQuery` for?**
To conditionally skip a query — for example, waiting for a dependent value like a user ID before fetching user-specific data.

**Q: How does RTK's Immer integration work?**
RTK wraps reducers in Immer's `produce`. You can write "mutating" code against the `state` draft; Immer produces a new immutable state object using structural sharing.

**Q: What is `nuqs`?**
A library that provides a `useState`-compatible API over URL search params, with type-safe serialization and batched updates, for Next.js and other frameworks.

---

## 🚩 Red Flags

- Putting API response data directly into a Redux slice without considering TanStack Query — suggests the candidate has not worked with modern server-state solutions.
- Saying "Context is a state manager" — demonstrates a conceptual gap about re-render behavior.
- Using `useEffect` to sync one state variable into another — derived state stored instead of computed.
- A global Zustand or Redux store with a property for every modal's open/closed state — ephemeral UI state does not belong in a global store.
- `queryKey: ["products"]` for queries that include filters or pagination — cache collision across different result sets.
- Not memoizing Context values — causes all consumers to re-render on every parent render.
- Fetching data inside a `useEffect` without a data-fetching library — reinventing loading/error/cache logic by hand.
- Describing Redux as the default answer without acknowledging simpler alternatives — signals cargo-cult architecture rather than principled decision-making.
- Storing computed values (totals, formatted strings, sorted arrays) in state — introduces sync bugs when the source data changes.
- Wrapping the entire application in a single Provider tree with one massive Context value — ensures every component re-renders on any change.
