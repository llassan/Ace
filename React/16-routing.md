# Client-Side Routing: React Router, Data Routers & Access Control

Client-side routing lets SPAs swap views without full page reloads by intercepting browser navigation and managing history programmatically. React Router v6/v7 is the de-facto standard, but the concepts — loaders, protected routes, RBAC gating — apply across every routing library. This file covers the mechanics, the modern data-router model, and the access-control patterns that come up in senior interviews.

> Note: Next.js App Router file-based routing is covered in **[08-nextjs.md]**; this file contrasts with it at the end.

---

## 🧠 How SPA Routing Works Under the Hood

### Q: How does the browser History API enable client-side routing without page reloads?

**Trade-off:** The History API gives you full URL control at zero network cost, but you must configure your server to serve `index.html` for every path or users get a 404 on hard refresh.

The two key primitives:

```ts
// Push a new entry — browser does NOT make a network request
history.pushState({ userId: 42 }, '', '/users/42');

// Replace current entry (no new history entry)
history.replaceState({}, '', '/users/42/edit');

// Browser fires this when user clicks back/forward
window.addEventListener('popstate', (event) => {
  console.log('navigated to', location.pathname, event.state);
});
```

React Router wraps these so you never call them directly. On every navigation it:
1. Calls `pushState` / `replaceState`
2. Matches the new pathname against the route tree
3. Re-renders the matched components

**Hash routing** (`/#/about`) avoids the server-rewrite problem because the hash fragment is never sent to the server, but it pollutes URLs, breaks anchor links, and is considered legacy.

**History routing** (`/about`) is canonical — but your CDN/server needs a catch-all rewrite:

```nginx
# nginx
location / {
  try_files $uri /index.html;
}
```

```js
// Vite dev server (vite.config.ts)
export default { server: { historyApiFallback: true } };
```

> 💡 Senior insight: The refresh-404 bug is the most common SPA deploy gotcha. In CI, always smoke-test a hard-refresh on a deep route, not just the homepage.

**Follow-ups they'll ask:**
- What happens with `popstate` and `pushState` in an iframe?
- How do you handle routing in an Electron app (no real server)?
- Can you SSR with hash routing? (No — hashes never reach the server.)

---

## 🗺️ React Router v6/v7 Core API

### Q: When do you choose `BrowserRouter` vs `createBrowserRouter`?

**Trade-off:** `BrowserRouter` is simpler to drop in, but `createBrowserRouter` (the data router) unlocks loaders, actions, deferred data, and co-located error boundaries — worth the extra setup for anything beyond a toy app.

```tsx
// ❌ Legacy: BrowserRouter — no loaders, no actions
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="users/:id" element={<UserDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

```tsx
// ✅ Modern: createBrowserRouter (v6.4+ / v7)
import { createBrowserRouter, RouterProvider } from 'react-router-dom';

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    errorElement: <RootError />,
    children: [
      { index: true, element: <Home /> },
      {
        path: 'users/:id',
        element: <UserDetail />,
        loader: userLoader,        // fetch before render
        errorElement: <UserError />,
      },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
```

### Q: Explain nested routes, `Outlet`, layout routes, and index routes.

**Trade-off:** Nested routes eliminate prop-drilling layout concerns and let each segment own its data, but deep nesting makes the route config harder to read — flatten aggressively beyond three levels.

```tsx
// Layout.tsx — renders shared chrome; Outlet = child route
import { Outlet, NavLink } from 'react-router-dom';

export function Layout() {
  return (
    <div>
      <nav>
        <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>
          Home
        </NavLink>
        <NavLink to="/settings">Settings</NavLink>
      </nav>
      <main>
        <Outlet />  {/* matched child renders here */}
      </main>
    </div>
  );
}
```

**Index route** matches the parent's exact path — the default child:

```tsx
{ path: 'settings', element: <SettingsLayout />, children: [
  { index: true, element: <GeneralSettings /> },  // /settings
  { path: 'security', element: <SecuritySettings /> },  // /settings/security
]}
```

**Layout route** — a route with no `path` that only contributes `element` (wrapping chrome):

```tsx
{
  element: <AuthenticatedLayout />,  // no path!
  children: [
    { path: 'dashboard', element: <Dashboard /> },
    { path: 'profile', element: <Profile /> },
  ],
}
```

### Q: How do you work with dynamic segments and search params?

```tsx
// :id is a dynamic segment
import { useParams, useSearchParams, Link } from 'react-router-dom';

function UserDetail() {
  const { id } = useParams<{ id: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = searchParams.get('tab') ?? 'overview';

  return (
    <div>
      <h1>User {id}</h1>
      <button onClick={() => setSearchParams({ tab: 'activity' })}>
        Activity
      </button>
    </div>
  );
}
```

> ⚠️ Gotcha: `useParams` returns `string | undefined` even when the param is required by the route — always provide a fallback or assert. With TypeScript you can wrap in a type-safe `useRequiredParams` helper.

### Q: `useNavigate` vs `Link` — when do you use each?

```tsx
import { useNavigate, Link } from 'react-router-dom';

function LoginForm() {
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await login(credentials);
    // Programmatic: after async work, or inside event handlers
    navigate('/dashboard', { replace: true });
  }

  return (
    <form onSubmit={handleSubmit}>
      {/* Declarative: prefer Link for anything the user clicks to navigate */}
      <Link to="/forgot-password">Forgot password?</Link>
      <button type="submit">Log in</button>
    </form>
  );
}
```

> 💡 Senior insight: Always prefer `<Link>` over `<button onClick={() => navigate(...)}>` for navigable destinations — it renders a real `<a>` tag, which supports right-click open-in-new-tab, cmd-click, and screen-reader semantics.

---

## ⚡ Data Router: Loaders, Actions & Deferred Data

### Q: Why do loaders beat fetch-in-useEffect?

**Trade-off:** Loaders start fetching at navigation time (parallel with the JS bundle), so by the time the component renders data is often ready. `useEffect` fetches after render, causing a waterfall. The downside: loaders live outside the component tree, which is a mental model shift.

```tsx
// userLoader runs before UserDetail renders
export async function userLoader({ params }: LoaderFunctionArgs) {
  const user = await fetchUser(params.id!);
  if (!user) throw new Response('Not Found', { status: 404 });
  return user;  // returned value available via useLoaderData
}

function UserDetail() {
  const user = useLoaderData() as User;  // already resolved — no loading state needed
  return <h1>{user.name}</h1>;
}
```

Timeline comparison:

```
useEffect model:  Navigate → Render skeleton → useEffect fires → fetch → re-render with data
Loader model:     Navigate → fetch starts → (JS loads) → render with data already ready
```

### Q: How does `defer` + `Await` enable streaming/progressive rendering?

**Trade-off:** `defer` lets you return fast critical data immediately while slow data streams in, improving Time to First Meaningful Paint. It adds complexity — you need `<Suspense>` boundaries and `<Await>` wrappers.

```tsx
import { defer, useLoaderData, Await } from 'react-router-dom';
import { Suspense } from 'react';

export function dashboardLoader() {
  return defer({
    user: fetchUser(),         // awaited — blocks render
    analytics: fetchAnalytics(), // deferred — streams in
  });
}

function Dashboard() {
  const { user, analytics } = useLoaderData() as {
    user: User;
    analytics: Promise<Analytics>;
  };

  return (
    <div>
      <h1>Welcome, {user.name}</h1>
      <Suspense fallback={<Spinner />}>
        <Await resolve={analytics} errorElement={<p>Analytics failed</p>}>
          {(data: Analytics) => <AnalyticsChart data={data} />}
        </Await>
      </Suspense>
    </div>
  );
}
```

### Q: How do actions work for mutations?

```tsx
// Form submissions hit the action before the loader re-runs
export async function updateUserAction({ request, params }: ActionFunctionArgs) {
  const formData = await request.formData();
  const name = formData.get('name') as string;
  await updateUser(params.id!, { name });
  return redirect(`/users/${params.id}`);
}

function EditUser() {
  const { id } = useParams();
  return (
    // React Router intercepts submit → calls action → revalidates loader
    <Form method="post" action={`/users/${id}/edit`}>
      <input name="name" />
      <button type="submit">Save</button>
    </Form>
  );
}
```

> 💡 Senior insight: `useNavigation().state` gives you `'idle' | 'loading' | 'submitting'` — use it to show optimistic UI or disable the submit button, replacing bespoke loading state in every form.

---

## 🔀 Code Splitting Routes

### Q: How do you lazy-load routes and why does it matter?

**Trade-off:** Route-based code splitting is the highest-ROI bundle optimization in an SPA — users only download code for routes they visit. The risk is a loading flash; mitigate with Suspense boundaries and prefetching.

```tsx
import { lazy, Suspense } from 'react';
import { createBrowserRouter } from 'react-router-dom';

// Each route chunk is a separate JS file
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings = lazy(() => import('./pages/Settings'));

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        path: 'dashboard',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <Dashboard />
          </Suspense>
        ),
      },
    ],
  },
]);
```

**v6.4+ lazy route object** — cleaner and supports loaders:

```tsx
const router = createBrowserRouter([
  {
    path: 'settings',
    lazy: async () => {
      const { Settings, loader } = await import('./pages/Settings');
      return { Component: Settings, loader };
    },
  },
]);
```

**Prefetch on hover** — eliminates the loading flash for likely navigations:

```tsx
function PrefetchLink({ to, children }: { to: string; children: React.ReactNode }) {
  const prefetch = () => {
    // Trigger dynamic import early so chunk is cached
    import(`./pages/${to}`).catch(() => {});
  };
  return (
    <Link to={to} onMouseEnter={prefetch} onFocus={prefetch}>
      {children}
    </Link>
  );
}
```

> See **[07-performance.md]** for bundle splitting strategy and tree-shaking patterns.

---

## 🔐 Protected Routes & Auth Guards

### Q: How do you implement a protected route that redirects to login?

**Trade-off:** A client-side auth guard is a UX convenience — it prevents rendering protected UI for unauthenticated users. It is not a security boundary; you must enforce authorization server-side on every API call.

```tsx
// AuthGuard.tsx
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function AuthGuard() {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return <FullPageSpinner />;

  if (!user) {
    // Preserve the attempted URL so we can redirect back after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
}
```

Route config:

```tsx
{
  element: <AuthGuard />,   // layout route — no path
  children: [
    { path: 'dashboard', element: <Dashboard /> },
    { path: 'profile', element: <Profile /> },
  ],
}
```

Return-to-URL after login:

```tsx
function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: Location })?.from?.pathname ?? '/dashboard';

  async function handleLogin() {
    await login(credentials);
    navigate(from, { replace: true });
  }
}
```

**Loader-based guard** (data router — preferred):

```tsx
export function requireAuth({ request }: LoaderFunctionArgs) {
  const user = getSessionUser();
  if (!user) {
    const params = new URLSearchParams([['from', new URL(request.url).pathname]]);
    throw redirect(`/login?${params}`);
  }
  return user;
}

// Compose into any loader
export async function dashboardLoader(args: LoaderFunctionArgs) {
  const user = await requireAuth(args);
  const data = await fetchDashboard(user.id);
  return { user, data };
}
```

> 💡 Senior insight: Loader-based guards run before rendering and work with SSR. Component-level guards always have a render flash window — even if brief, it can leak protected UI structure.

> ⚠️ Gotcha: Never store auth tokens in JavaScript-accessible storage for high-security apps — use httpOnly cookies so the token is invisible to client code entirely.

**Follow-ups they'll ask:**
- How do you handle token refresh mid-navigation?
- What if the user opens a protected route in a new tab with a stale session?
- How do you prevent the login redirect loop?

---

## 🛡️ RBAC / ABAC on the Client

### Q: How do you implement role-based and permission-based route gating?

**Trade-off:** Client-side RBAC provides fast, zero-flicker UX and avoids exposing routes to unauthorized users in the rendered HTML. But it is purely cosmetic security — a determined user can bypass it. Layer it over server enforcement, never substitute for it.

```tsx
// types/auth.ts
type Role = 'admin' | 'editor' | 'viewer';
type Permission = 'users:read' | 'users:write' | 'billing:read' | 'billing:write';

interface User {
  id: string;
  role: Role;
  permissions: Permission[];
}
```

```tsx
// hooks/usePermissions.ts
import { useAuth } from '../context/AuthContext';

export function usePermissions() {
  const { user } = useAuth();

  const hasPermission = (permission: Permission): boolean =>
    user?.permissions.includes(permission) ?? false;

  const hasRole = (role: Role): boolean => user?.role === role;

  const hasAnyPermission = (permissions: Permission[]): boolean =>
    permissions.some(p => hasPermission(p));

  return { hasPermission, hasRole, hasAnyPermission };
}
```

**`<RequirePermission>` pattern — declarative UI gating:**

```tsx
interface RequirePermissionProps {
  permission: Permission;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export function RequirePermission({ permission, fallback = null, children }: RequirePermissionProps) {
  const { hasPermission } = usePermissions();
  return hasPermission(permission) ? <>{children}</> : <>{fallback}</>;
}

// Usage — hides the button entirely, not just disables it
function UserTable() {
  return (
    <div>
      <DataTable />
      <RequirePermission permission="users:write">
        <AddUserButton />
      </RequirePermission>
    </div>
  );
}
```

**Route-level RBAC guard:**

```tsx
interface RoleGuardProps {
  allowedRoles: Role[];
}

export function RoleGuard({ allowedRoles }: RoleGuardProps) {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  if (!allowedRoles.includes(user.role)) return <Navigate to="/403" replace />;

  return <Outlet />;
}
```

```tsx
// Route config with role enforcement
{
  element: <RoleGuard allowedRoles={['admin']} />,
  children: [
    { path: 'admin', element: <AdminPanel /> },
    { path: 'admin/billing', element: <BillingAdmin /> },
  ],
}
```

**ABAC pattern** — attribute-based, more expressive than RBAC:

```tsx
type PolicyFn = (user: User, resource?: unknown) => boolean;

const policies: Record<string, PolicyFn> = {
  'billing:manage': (user) => user.permissions.includes('billing:write'),
  'user:edit': (user, resource: unknown) => {
    const target = resource as User;
    return user.role === 'admin' || user.id === target.id;  // own profile always editable
  },
};

export function can(user: User, action: string, resource?: unknown): boolean {
  return policies[action]?.(user, resource) ?? false;
}
```

> 💡 Senior insight: Ship permission lists from the server in the session/token (not role names alone) — it lets you grant fine-grained access without deploying code. Roles then become convenience groupings, not hard gates in the client.

> ⚠️ Gotcha: Never derive permissions client-side from role strings like `if (role === 'admin')` spread across the codebase — it's impossible to audit and breaks when roles evolve. Centralize policy in a single `can()` function.

> See **[10-security.md]** for server-side enforcement, JWT validation, and API authorization patterns.

---

## 🧭 Navigation Concerns

### Q: How do you block navigation when a form has unsaved changes?

**Trade-off:** `useBlocker` gives users a safety net against accidental data loss. It only works for in-app navigations — browser close/refresh needs `beforeunload`, which you must handle separately.

```tsx
import { useBlocker } from 'react-router-dom';
import { useState } from 'react';

function EditForm() {
  const [isDirty, setIsDirty] = useState(false);

  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      isDirty && currentLocation.pathname !== nextLocation.pathname
  );

  return (
    <div>
      <form onChange={() => setIsDirty(true)}>
        <input name="title" />
      </form>

      {blocker.state === 'blocked' && (
        <ConfirmDialog
          message="You have unsaved changes. Leave anyway?"
          onConfirm={() => blocker.proceed()}
          onCancel={() => blocker.reset()}
        />
      )}
    </div>
  );
}
```

Browser unload (hard refresh / tab close):

```tsx
useEffect(() => {
  if (!isDirty) return;
  const handler = (e: BeforeUnloadEvent) => { e.preventDefault(); };
  window.addEventListener('beforeunload', handler);
  return () => window.removeEventListener('beforeunload', handler);
}, [isDirty]);
```

### Q: How do you handle scroll restoration, 404s, and redirects?

**Scroll restoration** — React Router v6 does not restore scroll automatically in all cases:

```tsx
import { ScrollRestoration } from 'react-router-dom';

// Place once in your root layout — handles scroll on navigation
function RootLayout() {
  return (
    <>
      <ScrollRestoration
        getKey={(location) => {
          // Use pathname for most pages; preserve scroll for modals
          return location.pathname;
        }}
      />
      <Outlet />
    </>
  );
}
```

**404 — catch-all route:**

```tsx
{ path: '*', element: <NotFound /> }
// Always place last in the children array
```

**Redirects:**

```tsx
// Declarative redirect (component)
{ path: 'old-path', element: <Navigate to="/new-path" replace /> }

// Loader redirect (data router — preferred for auth/logic)
export function oldRouteLoader() {
  throw redirect('/new-path');
}
```

**Query state sync** — for filters, pagination, tabs synced to the URL:

```ts
// useSearchParams works, but for complex state consider nuqs
// See 06-state.md for nuqs patterns with React 19
```

### Q: How do you manage query params vs path params — when to use each?

- **Path params** (`/users/42`): required identifiers that define the resource. Bookmarkable and indexable.
- **Query params** (`/users?role=admin&page=2`): optional filters, sorts, pagination. Composable and shareable.
- **State** (`navigate('/login', { state: { from } })`): ephemeral, survives navigation but not bookmark/refresh.

---

## 🏗️ Route Config at Scale

### Q: How do you modularize routes in a large application?

**Trade-off:** Centralizing all routes in one file is readable at small scale but becomes a bottleneck for large teams. Module-owned route configs with a root aggregator scales better and co-locates loaders/components with features.

```
src/
  routes/
    index.ts           ← root router config
    auth/
      index.ts         ← auth route subtree
      LoginPage.tsx
      loader.ts
    dashboard/
      index.ts
      DashboardPage.tsx
      loader.ts
    admin/
      index.ts
      guard.ts
```

```tsx
// routes/dashboard/index.ts
import { RouteObject } from 'react-router-dom';
import { dashboardLoader } from './loader';
const DashboardPage = lazy(() => import('./DashboardPage'));

export const dashboardRoutes: RouteObject[] = [
  {
    path: 'dashboard',
    lazy: async () => {
      const { DashboardPage, loader } = await import('./DashboardPage');
      return { Component: DashboardPage, loader };
    },
    children: [
      { index: true, element: <Overview /> },
      { path: 'analytics', element: <Analytics /> },
    ],
  },
];
```

```tsx
// routes/index.ts — aggregator
import { createBrowserRouter } from 'react-router-dom';
import { authRoutes } from './auth';
import { dashboardRoutes } from './dashboard';
import { adminRoutes } from './admin';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    errorElement: <RootError />,
    children: [
      ...authRoutes,
      { element: <AuthGuard />, children: [...dashboardRoutes, ...adminRoutes] },
      { path: '*', element: <NotFound /> },
    ],
  },
]);
```

> 💡 Senior insight: Co-locate the loader with the page component — when the page moves, the loader moves with it. Avoid a single `loaders/` folder that mirrors pages; it's a maintenance trap.

---

## 🆚 TanStack Router & Next.js App Router

### Q: When would you choose TanStack Router over React Router?

**Trade-off:** TanStack Router has fully type-safe route params and search params (no casting needed), which eliminates an entire class of bugs in large TypeScript codebases. The ecosystem and community are smaller, and the API is more verbose.

```tsx
// TanStack Router: params and search are fully typed at the route definition
const userRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/users/$userId',
  validateSearch: (search) => z.object({ tab: z.string().optional() }).parse(search),
  loader: ({ params }) => fetchUser(params.userId),  // params.userId is string, not string|undefined
});
```

**Choose TanStack Router when:** TypeScript correctness is paramount, you have complex search param schemas, or you want built-in devtools with first-class TS support.

**Choose React Router when:** team familiarity, ecosystem size, and loader/action conventions match your mental model.

### Q: How does React Router differ from Next.js App Router?

| Concern | React Router (client) | Next.js App Router (server-first) |
|---|---|---|
| Route definition | JS config / JSX | File system (`app/page.tsx`) |
| Data fetching | Loaders (client-initiated) | Server Components (fetch in component) |
| Rendering | Client-side by default | Server-side by default |
| Code splitting | Manual `lazy()` | Automatic per segment |
| Auth guards | Client component or loader | Middleware (`middleware.ts`) |
| Streaming | `defer` + `Await` | `loading.tsx` + `Suspense` |
| Bundle size | Larger client JS | Smaller — server does more |

**Use React Router when:** you have a pure SPA, an existing CRA/Vite codebase, or a desktop/Electron app where server rendering is irrelevant.

**Use Next.js App Router when:** SEO, initial load performance, and server-side data access are first-class requirements.

> See **[08-nextjs.md]** for App Router file conventions, server actions, and the parallel/intercepting routes patterns.

---

## ⚡ Rapid-Fire

**Q: What is the difference between `<Link>` and `<a>`?**
`<Link>` intercepts clicks and uses `pushState`; `<a>` triggers a full page reload.

**Q: What does `replace` do in `navigate('/path', { replace: true })`?**
Replaces the current history entry instead of pushing a new one — the back button skips over it.

**Q: What is an index route?**
A child route with no path that renders at the parent's exact URL — the default child.

**Q: Why must you wrap `<Suspense>` around lazy routes?**
React throws a Promise on first render of a lazy component; Suspense catches it and shows the fallback until the chunk resolves.

**Q: What is the difference between `errorElement` and a try/catch in a loader?**
`errorElement` renders when the loader throws or rejects; try/catch lets the loader return a partial result instead of blowing up the route.

**Q: Can loaders run in parallel?**
Yes — sibling route loaders run concurrently; child loaders start only after their parent loader resolves (unless you `defer`).

**Q: How does `NavLink` differ from `Link`?**
`NavLink` receives an `isActive` / `isPending` callback so you can apply active styles without manual location comparison.

**Q: What is a splat route (`path: '*'`)?**
Matches any path not caught by earlier routes — use it for 404 pages.

**Q: Can you use React Router with React Native?**
Not directly — use `react-router-native` or React Navigation for mobile.

**Q: What does `useRouteError` do?**
Accesses the error thrown in a loader, action, or child component inside an `errorElement`.

---

## 🚩 Red Flags

- Fetching data in `useEffect` instead of loaders in a data-router app — misses the parallel fetch benefit.
- Treating client-side auth guards as security boundaries — the server must enforce every request.
- Putting all 50+ routes in a single flat `App.tsx` — no lazy loading, no co-location, no team scalability.
- Using `window.location.href = '/path'` for in-app navigation — forces a full page reload.
- Storing sensitive authorization logic only in the frontend — easy to bypass via browser devtools.
- Deriving permissions from role string comparisons scattered across components — impossible to audit.
- No `*` catch-all route — users see a blank page instead of a 404.
- Forgetting `beforeunload` when implementing unsaved-changes protection — `useBlocker` alone does not cover tab close.
- Nesting routes five or six levels deep — creates deeply coupled UI that is painful to refactor.
- Ignoring scroll position on navigation — users land mid-page on route change.
