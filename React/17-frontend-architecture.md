# Frontend Architecture: Structuring Large-Scale React Applications

Senior frontend engineers are evaluated not just on component skill but on how they design systems that survive team growth, feature churn, and organizational change. This guide covers folder structure, module boundaries, monorepos, design systems, micro frontends, and the team conventions that hold it all together — the architectural decisions that distinguish a lead from an individual contributor. For product/feature design end-to-end, see file 12; for build tooling and bundler internals, see file 19; for component quality and testing gates, see files 11 and 20.

---

## Folder Structure: By-Type vs By-Feature vs Feature-Sliced Design

### Q: How do you structure a large React application and why does it matter?

**By-type** (anti-pattern at scale):
```
src/
  components/
  hooks/
  services/
  utils/
  types/
```
Everything in `components/` grows to hundreds of files. A change to "checkout" touches files across four directories. Cognitive load explodes.

**By-feature** (pragmatic, most teams):
```
src/
  features/
    checkout/
      CheckoutFlow.tsx
      useCheckout.ts
      checkoutApi.ts
      checkout.test.ts
      index.ts           ← public API
    catalog/
    auth/
  shared/
    ui/                  ← generic, stateless UI primitives
    lib/                 ← utilities, formatters, hooks with no domain
    api/                 ← typed HTTP client
  app/
    router.tsx
    store.ts
    App.tsx
```

**Feature-Sliced Design (FSD)** — a stricter methodology with enforced layer ordering:
```
src/
  app/          ← initialization, providers, global styles
  pages/        ← route compositions, thin
  widgets/      ← composite UI blocks (Header, Sidebar)
  features/     ← user interactions (add-to-cart, auth-form)
  entities/     ← business objects (User, Product, Order)
  shared/       ← UI kit, lib, api, config
```

FSD enforces a strict dependency direction: layers may only import from layers below them. `features` cannot import from `widgets`; `entities` cannot import from `features`. This prevents circular coupling but requires team discipline and tooling to enforce.

> 💡 **Senior insight:** FSD is excellent for large teams with strong process. For teams under 10 engineers, by-feature with a clear `shared/` boundary delivers 80% of the benefit with 20% of the overhead. The most important principle is **colocation**: keep everything a feature needs (component, hook, API call, types, tests) in one directory so deleting a feature is a single `rm -rf`.

**Colocation principle:**
- Test files live next to the code they test
- Styles (CSS modules or styled components) live in the feature
- Types specific to a feature live in the feature
- Only truly shared, domain-agnostic code belongs in `shared/`

⚠️ **Gotcha:** The moment you create `shared/types/` for domain types, features start cross-importing and your boundaries dissolve. Domain types belong in `entities/` (FSD) or in the feature itself.

---

## Module Boundaries and Dependency Rules

### Q: How do you prevent features from becoming a tightly coupled ball of mud?

The dependency direction must be one-way:

```
shared/  ←  entities/  ←  features/  ←  pages/  ←  app/
```

Higher layers import lower layers. Lower layers never import upward. Features **never** import from each other's internals.

**The public API pattern — index.ts barrels:**
```ts
// features/checkout/index.ts  — the ONLY public surface
export { CheckoutFlow } from './CheckoutFlow';
export type { CheckoutState } from './types';
// Internal helpers, sub-components NOT exported
```

Other features or pages import only from the barrel:
```ts
// Good
import { CheckoutFlow } from '@/features/checkout';

// Bad — reaches into internals
import { useCheckoutValidation } from '@/features/checkout/hooks/useCheckoutValidation';
```

**Tooling to enforce this:**

`eslint-plugin-boundaries`:
```js
// .eslintrc.js
rules: {
  'boundaries/element-types': ['error', {
    default: 'disallow',
    rules: [
      { from: 'features', allow: ['shared', 'entities'] },
      { from: 'pages',    allow: ['shared', 'entities', 'features', 'widgets'] },
      { from: 'shared',   allow: ['shared'] },
    ]
  }]
}
```

`dependency-cruiser` for visualizing actual dependency graphs and failing CI when rules are violated.

> 💡 **Senior insight:** Barrel files (`index.ts`) have a performance gotcha covered in file 07 — bundlers that don't support tree-shaking well will pull in the entire barrel. In large apps, prefer explicit path imports for rarely-used exports, or ensure your bundler (Vite/webpack 5) handles tree-shaking correctly.

**Follow-ups they'll ask:**
- How do you handle shared state between features without direct imports?
- What's your strategy when two features genuinely need the same domain logic?
- How do you migrate a codebase that already has tangled imports?

---

## Feature-Based / Modular Architecture in Practice

### Q: Walk me through what a well-designed feature module looks like.

```
features/
  product-catalog/
    index.ts                  ← public API (exports only)
    ProductCatalog.tsx         ← top-level feature component
    ProductCard.tsx            ← internal component
    CatalogFilters.tsx
    useCatalog.ts              ← feature-level state/logic hook
    catalogApi.ts              ← API calls for this feature
    catalogSlice.ts            ← Redux/Zustand slice (if applicable)
    catalog.types.ts           ← feature-local types
    ProductCatalog.test.tsx
    ProductCard.test.tsx
    useCatalog.test.ts
    __mocks__/
      catalogApi.ts
```

**When to extract to shared:**
- When 3+ features need the same component or utility
- When the abstraction is genuinely domain-agnostic (a `DatePicker`, not a `CheckoutDatePicker`)
- Never pre-emptively — move code to shared when the duplication is proven, not anticipated

⚠️ **Gotcha:** "Shared" becomes a dumping ground. Enforce a contribution gate: new additions to `shared/` require review from 2+ engineers and must have no feature-specific domain logic.

---

## Monorepos: Why, When, and Trade-offs

### Q: When would you choose a monorepo over polyrepo?

**Monorepo advantages:**
- Atomic changes across packages (update a shared component and all consumers in one PR)
- Consistent tooling (one ESLint config, one TypeScript config to maintain)
- Simplified code sharing without npm publish cycles
- Cross-package refactoring with IDE/TypeScript support

**Monorepo workspace layout:**
```
my-platform/
  apps/
    web/               ← main React SPA
    admin/             ← internal tools app
    mobile-web/
  packages/
    ui/                ← design system components
    utils/             ← shared utilities
    api-client/        ← generated/typed API client
    config/            ← shared ESLint, TS, Tailwind configs
  turbo.json           ← or nx.json
  pnpm-workspace.yaml
```

**Nx vs Turborepo:**

| | Turborepo | Nx |
|---|---|---|
| Caching | Remote + local, fast | Remote + local, powerful |
| Affected graph | `--filter` manual | Automatic affected detection |
| Generators | No | Yes (scaffolding) |
| Learning curve | Low | Medium-High |
| Opinionation | Low | High |
| Best for | Simpler setups, JS-first | Large enterprise, polyglot |

```bash
# Turborepo: run only affected packages
turbo run build --filter=...[HEAD^1]

# Nx: run affected
nx affected --target=build
```

**Versioning strategies:**
- **Fixed/lockstep** (Lerna, Nx): all packages share a version number. Simple, less flexible.
- **Independent**: each package versioned separately. Required for packages published to npm with different release cadences.

**Monorepo downsides (be honest):**
- CI pipelines become complex; affected computation can have false positives
- Large repos slow down `git` operations and IDE indexing
- Accidental coupling is easier — a "quick import" from another app can bypass boundaries
- Onboarding complexity increases

> 💡 **Senior insight:** Monorepos solve organizational problems (shared code, atomic changes) but create operational ones (CI complexity). The right answer depends on team size and how much code genuinely needs sharing. A single-app repo with an internal `packages/` directory gives you most of the benefit before you need full monorepo tooling.

---

## Design Systems and Component Libraries

### Q: How do you build and govern a design system for a product organization?

**Architecture layers:**

```
Design Tokens
    ↓
Primitives (Button, Input, Modal — headless or minimally styled)
    ↓
Composed Components (SearchBar = Input + Icon + Button)
    ↓
Page-level patterns / Templates
```

**Design tokens** are the single source of truth for visual constants:
```ts
// tokens.ts — generated from Figma or defined manually
export const tokens = {
  color: {
    primary:   { 50: '#eff6ff', 500: '#3b82f6', 900: '#1e3a5f' },
    semantic:  { error: '#ef4444', success: '#22c55e' },
  },
  spacing: { 1: '4px', 2: '8px', 4: '16px', 8: '32px' },
  radius:  { sm: '4px', md: '8px', full: '9999px' },
} as const;
```

**Headless + styled split:**
- Headless libraries (Radix UI, Headless UI, React Aria) handle accessibility, keyboard nav, and ARIA without imposing styles
- Your design system wraps headless primitives with your tokens and variant API
- This separates correctness (a11y, behavior) from aesthetics

```tsx
// Primitive using Radix (headless) + your tokens
import * as DialogPrimitive from '@radix-ui/react-dialog';

export const Modal = ({ children, title, ...props }) => (
  <DialogPrimitive.Root {...props}>
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className={styles.overlay} />
      <DialogPrimitive.Content className={styles.content}>
        <DialogPrimitive.Title>{title}</DialogPrimitive.Title>
        {children}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  </DialogPrimitive.Root>
);
```

**Distribution:**
- Internal monorepo: workspace package (`packages/ui`), no publish step
- External/multi-org: semantic versioned npm package; use Changesets for changelog automation

**Governance model:**
- Contribution guide with clear criteria for what belongs in shared vs feature
- Designated maintainers with final review authority
- RFC process for breaking changes
- Adoption metrics (usage, Storybook traffic)

**Storybook as living documentation:**
```tsx
// Button.stories.tsx
export default {
  title: 'Primitives/Button',
  component: Button,
  argTypes: { variant: { control: 'select', options: ['primary', 'secondary', 'ghost'] } },
} satisfies Meta<typeof Button>;

export const Primary: Story = { args: { variant: 'primary', children: 'Click me' } };
export const Disabled: Story = { args: { disabled: true, children: 'Disabled' } };

// Interaction test
export const ClickFeedback: Story = {
  play: async ({ canvasElement }) => {
    const btn = within(canvasElement).getByRole('button');
    await userEvent.click(btn);
    await expect(btn).toHaveBeenCalledTimes(1);
  },
};
```

Storybook serves as a dev sandbox (build components in isolation), visual regression baseline (Chromatic), interaction test runner (Storybook Test), and the reference for designers and engineers. A11y is enforced via `@storybook/addon-a11y` — see file 11 for accessibility patterns.

> 💡 **Senior insight:** The hardest design system problem is adoption, not implementation. Teams will bypass the system if it doesn't meet their velocity needs. Solve this with: fast contribution paths, a "needs" channel, and visible executive buy-in. The system must be easier to use than to circumvent.

---

## Micro Frontends: When They Help and When They Hurt

### Q: Should we use micro frontends? What's your take?

**The honest senior answer: most teams should not.**

Micro frontends solve an organizational problem: multiple teams need to deploy their UI independently without coordinating releases. They introduce significant complexity that is only justified at a certain organizational scale.

**When MFEs genuinely help:**
- Truly independent teams that cannot coordinate releases (Conway's Law alignment)
- Heterogeneous tech stacks that must coexist during a long migration
- Very large surfaces (internal portals with 10+ product teams)

**Integration approaches:**

```
Build-time integration  — packages imported as npm dependencies
  Pros: simple, type-safe, tree-shakeable
  Cons: not independent deployment; any change requires republish + redeploy

Runtime integration (Module Federation)  — see file 19 for mechanics
  Pros: independent deploy, lazy load remote modules at runtime
  Cons: complex, runtime errors if versions mismatch

iframes  — true isolation
  Pros: complete isolation, any tech stack
  Cons: UX limitations, communication overhead, no shared state

Web Components  — custom elements with shadow DOM
  Pros: framework-agnostic
  Cons: poor React interop, SSR limitations
```

**Module Federation shared dependency problem:**
```js
// webpack.config.js — host app
new ModuleFederationPlugin({
  shared: {
    react: { singleton: true, requiredVersion: '^18.0.0' },
    'react-dom': { singleton: true, requiredVersion: '^18.0.0' },
  }
});
```
If two remotes ship different React versions and `singleton: true` is not set, you get multiple React instances — React Context will not cross the boundary, hooks will throw, and portals will break. React Context is fundamentally broken across MFE boundaries without careful shared-singleton configuration.

**Routing across MFEs:** each remote owns its sub-routes; the shell handles top-level routing and delegates. State sharing must go through explicit contracts (custom events, a shared event bus, URL, or a shared Zustand store loaded as a singleton).

⚠️ **Gotcha:** MFEs do not eliminate coordination — they move it from code to runtime contracts. API contracts, shared dependency versions, and shell/remote protocol must still be coordinated. You trade compile-time safety for deploy-time flexibility.

**Follow-ups they'll ask:**
- How do you handle auth tokens across MFE boundaries?
- What's your strategy for shared error boundaries?
- How do you test MFE integration?

---

## Cross-Cutting Architecture Concerns

### Config and environment management:
```ts
// config/env.ts — centralized, typed, validated at startup
const env = z.object({
  VITE_API_URL:         z.string().url(),
  VITE_FEATURE_FLAGS:   z.string().optional(),
  VITE_SENTRY_DSN:      z.string().optional(),
}).parse(import.meta.env);

export const config = {
  apiUrl: env.VITE_API_URL,
  sentryDsn: env.VITE_SENTRY_DSN,
} as const;
```

### Feature flags placement:
- Runtime flags (LaunchDarkly, Unleash) belong in a `shared/flags/` layer with a typed hook: `useFlag('new-checkout-flow')`
- Components should not call the flag SDK directly — indirect through the abstraction so the SDK can be swapped
- Flag evaluation in the API layer (server-driven) vs client layer is a separate architectural decision

### Error and observability boundaries:
```tsx
// app/ErrorBoundary.tsx
class RootErrorBoundary extends React.Component {
  componentDidCatch(error: Error, info: ErrorInfo) {
    Sentry.captureException(error, { extra: { componentStack: info.componentStack } });
  }
  // ...
}
// Feature-level boundaries for graceful degradation without full-page crashes
```

### i18n architecture:
- Namespace per feature (`checkout`, `catalog`, `common`) to enable lazy loading of translation bundles
- Type-safe keys via `i18next-parser` or `react-i18next` with TypeScript declarations
- Locale detection: URL segment > `Accept-Language` header > user preference stored in profile

### The app shell:
The shell is the thin top-level wrapper: router, global providers (auth, theme, query client, error boundary), analytics init, and feature flag bootstrap. It should contain almost no business logic.

---

## Scaling the Team and Codebase

### Q: How do you keep a large codebase maintainable as the team grows?

**CODEOWNERS:**
```
# .github/CODEOWNERS
/src/features/checkout/     @team-commerce
/src/features/auth/         @team-platform
/packages/ui/               @team-design-system
```
CODEOWNERS routes PRs to the right reviewers automatically and creates accountability for module quality.

**Mandatory gates (CI enforced — see file 20):**
```
lint → typecheck → unit tests → integration tests → build
```
No merge without green gates. Lint and format are non-negotiable: discussion about style in code review is a waste of senior engineering time.

**Architecture Decision Records (ADRs):**
```markdown
# ADR-007: Adopt Zustand over Redux Toolkit for feature-local state

## Status: Accepted — 2025-03-12

## Context
Redux Toolkit adds boilerplate for isolated feature state that does not
need global access. Feature teams are copying state management code
rather than extracting shared patterns.

## Decision
Zustand for feature-local and cross-feature state. RTK Query for
server-state caching. Redux retained for global auth/session state.

## Consequences
Positive: less boilerplate, faster feature development.
Negative: two state libraries to onboard; requires clear guidance on
which to use in which context.
```

ADRs live in `/docs/adr/` and are linked from relevant code. They answer "why does this code look like this?" for future engineers.

**Incremental migration — strangler pattern:**
```
Old system ──────────────────────────── New system
     ↓                                      ↑
  /legacy/*  ←  Routing proxy  →  /new-feature/*
```
New features are built in the target architecture. Old code is migrated opportunistically, one feature at a time, behind the same URL structure. Never rewrite everything at once.

**Tech debt management:**
- Tag debt with `// TODO(ADR-012): migrate to new API` not generic TODOs
- Track debt in the backlog with business impact context, not just technical description
- Budget 20% of sprint capacity for debt — protect it from feature pressure

---

## API Layer Architecture

### Q: How do you structure the API/data layer in a large frontend?

A typed, feature-agnostic transport layer prevents API concerns from leaking into components. See file 15 for full data-fetching patterns.

```
shared/
  api/
    client.ts          ← axios/fetch wrapper with interceptors, auth headers
    types.ts           ← shared API error types, pagination shapes

features/
  catalog/
    catalogApi.ts      ← feature-specific queries, uses shared client
```

```ts
// shared/api/client.ts
const apiClient = axios.create({ baseURL: config.apiUrl });

apiClient.interceptors.request.use(req => {
  req.headers.Authorization = `Bearer ${getAuthToken()}`;
  return req;
});

apiClient.interceptors.response.use(
  res => res,
  async err => {
    if (err.response?.status === 401) await refreshToken();
    return Promise.reject(toApiError(err));
  }
);

export { apiClient };
```

```ts
// features/catalog/catalogApi.ts
import { apiClient } from '@/shared/api/client';
import type { Product, PaginatedResponse } from '@/shared/api/types';

export const catalogApi = {
  getProducts: (filters: ProductFilters): Promise<PaginatedResponse<Product>> =>
    apiClient.get('/products', { params: filters }).then(r => r.data),

  getProductById: (id: string): Promise<Product> =>
    apiClient.get(`/products/${id}`).then(r => r.data),
};
```

The feature's React Query hooks wrap `catalogApi` — components never call `apiClient` directly. This makes mocking trivial, transport swappable, and the domain model independent of HTTP concerns.

---

## ⚡ Rapid-Fire

- **Barrel files (index.ts) — good or bad?** Good for enforcing public API boundaries. Bad when they include large unused exports that prevent tree-shaking. Use with bundler analysis.
- **When does a component belong in shared vs a feature?** Shared when 3+ features need it and it has no domain knowledge. Otherwise, start in the feature.
- **How do you prevent shared from becoming a dumping ground?** Contribution gate: PR requires 2 reviewers from different teams, no domain types allowed.
- **Monorepo vs polyrepo for a team of 8?** Monorepo with Turborepo if you have more than one app sharing code. Polyrepo if apps are truly independent.
- **Is FSD worth adopting?** Worth it for teams 15+ engineers who will invest in tooling and education. For smaller teams, by-feature with a shared layer delivers the same result with less ceremony.
- **Micro frontends for a team of 20?** Almost certainly no. Build a well-structured monorepo first.
- **Where do feature flags live?** In `shared/flags/` behind a typed hook. Features never import the flag SDK directly.
- **How do you enforce module boundaries in CI?** `eslint-plugin-boundaries` fails the lint step on invalid imports. `dependency-cruiser` generates a visual graph and can be configured to fail on rule violations.
- **Storybook vs unit tests — which do you choose?** Both serve different purposes. Storybook catches visual and a11y regressions; unit tests catch logic errors. Interaction tests in Storybook can replace some integration tests for UI flows.
- **How do you handle breaking changes to a shared component?** Semantic versioning + Changesets for changelog. Codemods for automated migration when possible. Deprecation period with console warnings before removal.

---

## 🚩 Red Flags

- "We put everything in a `components/` folder sorted alphabetically" — no feature encapsulation, impossible to scale
- "Features import directly from other features' source files" — tight coupling, no module boundaries
- "We'll figure out the architecture later, let's ship first" — technical debt compounds; architecture is hardest to change retroactively
- "We adopted micro frontends to let teams move faster" — almost always the wrong solution; the coordination cost of MFEs usually exceeds the benefit for teams under ~50 engineers
- "Our design system is a folder of copy-pasted components" — not a design system, no governance, will diverge immediately
- "We don't have ADRs because we move too fast" — fast teams make the most decisions; ADRs are most valuable under velocity pressure, not least
- "Shared is where we put stuff no one owns" — shared without ownership becomes a maintenance black hole
- "We'll add ESLint boundaries once the codebase stabilizes" — by then, violations are load-bearing; enforce from day one
- "Our monorepo has no affected graph analysis, CI runs everything on every PR" — signals lack of investment in developer experience; will bottleneck the team as the repo grows
- Treating monorepo adoption as the solution to organizational problems — monorepos are a tooling choice, not a substitute for team structure or API contracts
