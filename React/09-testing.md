# React Testing — Strategy, Philosophy, and Execution

Testing in React is not about coverage numbers or tool choices — it is about shipping confident, maintainable software. Senior engineers own the testing culture: they define what to test, set the boundaries between test types, and make the call when a test causes more harm than good.

---

## Testing Philosophy

### Q: What is the "testing trophy" and how does it differ from the testing pyramid?

The classical testing pyramid (many unit → some integration → few e2e) was defined in a server-side context where integration was expensive. Kent C. Dodds's **testing trophy** re-weights for frontend work:

```
        /\
       /e2e\          ← fewest, highest confidence, highest cost
      /------\
     / integr.\       ← the fat middle — the sweet spot for React
    /----------\
   /   unit     \     ← targeted, fast, for pure logic only
  /--------------\
 /  static (TS,  \    ← free confidence via compiler + linting
/   lint, types)  \
```

The key insight: **integration tests give you the highest confidence-per-dollar** for UI code. A test that renders a `<CheckoutForm />` with real child components, a mocked network layer, and real user interactions catches far more real bugs than fifty unit tests on each child in isolation.

> 💡 Senior insight: When a team asks "what is our coverage target?" redirect to "what is our confidence-per-test-maintenance-cost ratio?" Coverage is an output metric; confidence is the outcome you care about.

**Follow-ups they'll ask:**
- When would you lean back toward unit tests? For pure transformation functions, algorithmic logic, date formatting utilities — anything with many input permutations but no UI.
- When would you add more e2e? For critical user journeys (checkout, login, sign-up) where the cost of a prod bug exceeds the cost of a slow CI suite.

---

### Q: What does "test behavior, not implementation" mean in practice?

It means your tests should survive a refactor. If you rename a state variable, extract a hook, or swap `useState` for `useReducer`, zero tests should break — unless the behavior actually changed.

**Implementation detail tests (avoid):**
- Asserting on component state directly
- Asserting on a specific CSS class name used for styling logic
- Checking that a specific child component was rendered by name
- Mocking and asserting on internal module functions

**Behavior tests (prefer):**
- The user sees a success message after form submission
- The button is disabled while a request is in flight
- An error banner appears when the API returns 500
- Keyboard navigation reaches the modal close button

⚠️ **Gotcha:** Shallow rendering (Enzyme's `shallow()`) is the canonical implementation-detail trap. It renders only one level deep and forces you to couple tests to component hierarchy. This is why RTL deliberately does not expose a shallow render API.

---

### Q: What should you NOT test?

Knowing what to skip is as important as knowing what to cover.

**Do not test:**
- Third-party library internals (React Router, React Query — test that your app uses them correctly, not that they work)
- Styling details that have no functional meaning
- Internal state that never surfaces to the user
- Things already covered by TypeScript (null checks, wrong prop types)
- Getters/setters with no logic

**Cost/confidence trade-off:** Every test has a carrying cost — it must be read, maintained, and updated when requirements change. A brittle test that breaks on every refactor trains engineers to treat failing tests as noise. **Brittle tests are worse than no tests** because they erode trust in the entire suite.

> 💡 Senior insight: If your team is scared to delete a failing test because "it might be catching something real," your test suite has already failed. Tests should be trusted or removed.

---

## React Testing Library

### Q: Walk me through RTL's guiding principles and query priority.

RTL's north star is from the docs: *"The more your tests resemble the way your software is used, the more confidence they can give you."*

This manifests in query priority — use queries in this order:

| Priority | Query | Why |
|---|---|---|
| 1 | `getByRole` | Mirrors accessibility tree — doubles as a11y check |
| 2 | `getByLabelText` | Form elements — tests label association |
| 3 | `getByPlaceholderText` | Fallback for inputs without labels |
| 4 | `getByText` | Static text content |
| 5 | `getByDisplayValue` | Current value of form fields |
| 6 | `getByAltText` | Images |
| 7 | `getByTitle` | Tooltip-bearing elements |
| 8 | `getByTestId` | **Last resort** — adds no a11y signal |

```tsx
// Bad — testId tells you nothing about accessibility
const btn = screen.getByTestId('submit-btn');

// Good — if this passes, a screen reader user can find this button
const btn = screen.getByRole('button', { name: /submit order/i });
```

**Query variants:**
- `getBy*` — throws if not found (use for elements that must be present)
- `queryBy*` — returns null if not found (use for asserting absence)
- `findBy*` — async, returns a promise (use for elements that appear after async work)

> 💡 Senior insight: Leaning on `getByRole` is a passive a11y audit. If you cannot query an element by role and name, neither can a screen reader. Tests that use role queries often surface missing `aria-label` or broken semantic HTML before dedicated a11y scans do.

---

### Q: Why prefer `userEvent` over `fireEvent`?

`fireEvent` dispatches a single synthetic DOM event. `userEvent` (v14+) simulates the full browser interaction sequence — pointer events, focus, keyboard events — much closer to how a real user interacts.

```tsx
import userEvent from '@testing-library/user-event';

// Bad — only fires a click event, skips focus, pointer, etc.
fireEvent.click(screen.getByRole('button', { name: /submit/i }));

// Good — simulates the full interaction chain
const user = userEvent.setup();
await user.click(screen.getByRole('button', { name: /submit/i }));
```

`userEvent.setup()` creates an isolated instance with its own clock and pointer state — required for tests that use fake timers.

⚠️ **Gotcha:** `userEvent` v14 is fully async. All methods return promises — always `await` them. Forgetting an `await` leads to assertions running before interactions complete, causing intermittent failures.

---

## Async Testing

### Q: How do you handle async behavior — loading, error, and success states?

Use `findBy*` for elements that appear after async work, and `waitFor` for assertions on existing elements that change asynchronously.

```tsx
it('shows user data after fetch resolves', async () => {
  const user = userEvent.setup();
  render(<UserProfile userId="123" />);

  // Assert loading state is visible immediately
  expect(screen.getByText(/loading/i)).toBeInTheDocument();

  // findBy* waits up to 1000ms by default
  const heading = await screen.findByRole('heading', { name: /vikash kumar/i });
  expect(heading).toBeInTheDocument();

  // Loading state should be gone
  expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
});

it('shows error state on API failure', async () => {
  // MSW handler overridden to return 500 for this test
  server.use(
    http.get('/api/user/:id', () => HttpResponse.error())
  );

  render(<UserProfile userId="123" />);
  const error = await screen.findByRole('alert');
  expect(error).toHaveTextContent(/failed to load/i);
});
```

### Q: What does an `act()` warning mean and how do you fix it properly?

The warning `Warning: An update to X inside a test was not wrapped in act(...)` means React processed a state update after your test assertions ran — the test finished before async work completed.

**Causes:**
- Unresolved promises after test ends
- Missing `await` on `userEvent` calls
- Timer-based state updates not controlled by fake timers
- Effects that run after the component unmounts

**Fix properly — do not suppress:**
```tsx
// Wrong — wrapping in act() manually to silence the warning
act(() => { /* ... */ });

// Right — find the root cause: what state update is completing after assertions?
// Usually means: await the user interaction, or await a findBy query,
// or flush fake timers before asserting.

it('shows result after debounced search', async () => {
  const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
  jest.useFakeTimers();

  render(<SearchBox />);
  await user.type(screen.getByRole('searchbox'), 'react');
  jest.advanceTimersByTime(300); // flush debounce

  await screen.findByText(/5 results/i);
  jest.useRealTimers();
});
```

> 💡 Senior insight: Wrapping things in `act()` to silence warnings without understanding the root cause is a code smell. It indicates the test is not actually waiting for real async boundaries. Hunt the root cause — it almost always reveals a real race condition or improper cleanup.

---

## Mocking Strategy

### Q: Why use MSW instead of `jest.mock` on fetch/axios?

`jest.mock` on network modules tests your mocking code, not your integration. It patches at the module level and leaks into test setup, making tests order-dependent and fragile.

**MSW (Mock Service Worker)** intercepts at the network level using a Service Worker in the browser or `msw/node` in Node. Your application code runs exactly as it would in production — `fetch`, `axios`, `React Query`, `SWR` all work normally.

```tsx
// src/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/users/:id', ({ params }) => {
    return HttpResponse.json({ id: params.id, name: 'Vikash Kumar' });
  }),
];

// src/mocks/server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);

// vitest.setup.ts
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

Override handlers per-test for error cases:
```tsx
server.use(
  http.post('/api/orders', () => new HttpResponse(null, { status: 500 }))
);
```

⚠️ **Gotcha:** Setting `onUnhandledRequest: 'error'` is critical. Without it, MSW silently passes unmatched requests through (or drops them), hiding missing handler definitions until production.

**Follow-ups they'll ask:**
- When would you still use `jest.mock`? For third-party modules with side effects (e.g., `react-router`'s `useNavigate`), browser APIs (`localStorage`, `IntersectionObserver`), or pure utility modules.

---

### Q: How do you make components testable through dependency injection?

Avoid hardcoded dependencies inside components. Pass services, clients, or callbacks as props or context so tests can substitute them.

```tsx
// Hard to test — hardcoded fetch
function UserCard({ userId }: { userId: string }) {
  const { data } = useQuery({ queryKey: ['user', userId], queryFn: () => fetch(`/api/users/${userId}`).then(r => r.json()) });
  return <div>{data?.name}</div>;
}

// Testable — queryFn injected or MSW intercepts the predictable URL
// With MSW, no injection needed — network layer is the seam
```

For non-network dependencies (analytics, feature flags, date providers):
```tsx
interface Props {
  now?: () => Date; // default: () => new Date()
}

function CountdownTimer({ now = () => new Date() }: Props) { /* ... */ }

// In test:
render(<CountdownTimer now={() => new Date('2026-01-01')} />);
```

---

## Testing Hooks

### Q: Should you test custom hooks directly or through a component?

**Default: test through a component.** A hook that exists to serve a component should be tested through that component's behavior. This gives you confidence the hook works in its real context.

**Use `renderHook` when:**
- The hook is a reusable utility consumed by many components
- The component is complex and the hook behavior is hard to trigger through the UI
- You need to test the hook's return values across many input permutations

```tsx
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

it('increments counter', () => {
  const { result } = renderHook(() => useCounter(0));

  act(() => {
    result.current.increment();
  });

  expect(result.current.count).toBe(1);
});
```

For hooks that use context or React Query, pass a wrapper:
```tsx
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
);

const { result } = renderHook(() => useUserData('123'), { wrapper });
```

> 💡 Senior insight: If you find yourself reaching for `renderHook` for every hook, it is a signal your tests are drifting toward implementation detail. The question is always: "what observable behavior does this hook produce for its consumer?"

---

## Jest vs Vitest

### Q: Why are teams migrating from Jest to Vitest?

| Concern | Jest | Vitest |
|---|---|---|
| ESM support | Complex — requires Babel or experimental VM | Native ESM out of the box |
| Speed | Single-threaded by default | Multi-threaded with worker threads |
| Config | Separate `jest.config.js` | Shares `vite.config.ts` — no duplication |
| TypeScript | Requires `ts-jest` or Babel transform | Native via Vite's pipeline |
| Watch mode | Slower rebuild | Near-instant HMR-based re-runs |
| API compatibility | Source | ~100% compatible — low migration cost |

**Vitest config essentials:**
```ts
// vite.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      exclude: ['src/mocks/**', '**/*.d.ts'],
    },
    globals: true, // optional: avoids importing describe/it/expect everywhere
  },
});
```

⚠️ **Gotcha:** `globals: true` requires adding `"types": ["vitest/globals"]` to `tsconfig.json`. Without it, TypeScript will complain about `describe` and `it` not being defined.

---

## Component vs Integration vs E2E

### Q: Where does each test type add the most value?

**Unit tests** — pure functions, algorithmic logic, edge-case-heavy utilities. Run in milliseconds. No DOM needed.

**Integration tests (RTL)** — the primary workhorse. Render a feature component with real children, mocked network (MSW), real router context. Catches wiring bugs, prop threading mistakes, context misuse.

**E2E tests (Playwright / Cypress)** — full browser, real server (or a staging server). Tests critical journeys end-to-end: auth flow, checkout, form submission with real DB writes.

### Q: What makes Playwright the right choice for e2e today?

Playwright's key advantages: auto-waiting (no manual `waitForElement` chains), multi-browser support (Chromium, Firefox, WebKit) from one config, built-in network interception, and a dedicated test runner with built-in parallelism.

```ts
// playwright.config.ts
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
});

// e2e/checkout.spec.ts
import { test, expect } from '@playwright/test';

test('user can complete checkout', async ({ page }) => {
  await page.goto('/cart');

  // Playwright auto-waits for the button to be visible and enabled
  await page.getByRole('button', { name: /proceed to checkout/i }).click();
  await page.getByLabel(/card number/i).fill('4242 4242 4242 4242');
  await page.getByRole('button', { name: /place order/i }).click();

  await expect(page.getByRole('heading', { name: /order confirmed/i })).toBeVisible();
});
```

**Network interception in Playwright:**
```ts
await page.route('**/api/payment', async route => {
  await route.fulfill({ json: { status: 'success', orderId: 'ORD-001' } });
});
```

**Flakiness control strategies:**
- Never use fixed `page.waitForTimeout()` — use `expect(locator).toBeVisible()`
- Set `retries: 2` in CI only — local retries hide real bugs
- Use `trace: 'on-first-retry'` to capture exactly what happened on the flaky run
- Quarantine persistently flaky tests into a separate suite tagged `@flaky` to prevent them from blocking CI

---

## Coverage

### Q: Why is 100% coverage a trap?

Coverage measures which lines were executed, not whether behavior was correctly verified. A test can execute a line without asserting anything meaningful about it.

```tsx
// 100% line coverage — but is the error case tested? No.
it('calls the function', () => {
  render(<Widget />);
  // No assertions — just renders
});
```

**What coverage tells you:** Which code paths have not been touched by any test. Useful for finding untested branches.

**What coverage does not tell you:** Whether your tests would catch a regression. A test can cover a line and still miss the bug.

> 💡 Senior insight: A pragmatic target is 70-80% statement coverage with a focus on critical paths. The marginal value of going from 80% to 95% is almost always lower than investing in better integration tests or e2e coverage of high-risk flows.

**Mutation testing (Stryker):** The honest measure of test suite quality. Stryker introduces deliberate code mutations (flips `>` to `>=`, deletes a return statement) and checks whether your tests catch them. A test suite with 90% coverage but 40% mutation score is mostly asserting nothing.

---

## Snapshot Tests

### Q: When are snapshot tests worth using?

Snapshot tests assert that rendered output does not change unexpectedly. They are low-effort to write but carry hidden costs at scale.

**The good:** Catching unintended changes to stable, low-churn components (design system primitives, icon sets, serialized data shapes).

**The bad:** Large snapshots are reviewed by no one. When they break, engineers update them with `--updateSnapshot` without reading the diff. They become a test suite liability rather than an asset.

**Inline snapshots** are better — the expected value lives next to the assertion and is small enough to review:
```tsx
it('renders badge with correct text', () => {
  render(<Badge count={5} />);
  expect(screen.getByText('5')).toMatchInlineSnapshot(`
    <span
      class="badge"
    >
      5
    </span>
  `);
});
```

⚠️ **Gotcha:** Never snapshot an entire page or large component tree. If the snapshot spans more than ~20 lines, it will be blindly updated. Prefer behavioral assertions for large components.

---

## Testing Context, Redux, and React Query

### Q: How do you handle providers in tests without repeating boilerplate?

Create a custom `render` utility that wraps the real app providers:

```tsx
// src/test/utils.tsx
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { createStore } from '../store';

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialRoute?: string;
  preloadedState?: Partial<RootState>;
}

function AllProviders({
  children,
  initialRoute = '/',
  preloadedState,
}: { children: React.ReactNode } & CustomRenderOptions) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }, // disable retries in tests
  });
  const store = createStore(preloadedState);

  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[initialRoute]}>
          {children}
        </MemoryRouter>
      </QueryClientProvider>
    </Provider>
  );
}

export function renderWithProviders(ui: React.ReactElement, options: CustomRenderOptions = {}) {
  const { initialRoute, preloadedState, ...renderOptions } = options;
  return render(ui, {
    wrapper: (props) => <AllProviders {...props} initialRoute={initialRoute} preloadedState={preloadedState} />,
    ...renderOptions,
  });
}
```

> 💡 Senior insight: Setting `retry: false` on QueryClient in tests is critical. Without it, React Query will retry failed requests up to 3 times, causing tests to time out and producing confusing `act()` warnings.

**Testing TanStack Query specifically:**
```tsx
it('displays user data from query', async () => {
  // MSW handler returns the user — no mocking of useQuery itself
  renderWithProviders(<UserProfile userId="123" />);

  await screen.findByText('Vikash Kumar');
});
```

---

## Visual Regression and Accessibility Testing

Visual regression testing (Percy, Chromatic) and automated a11y testing are covered in depth in file `11-accessibility-and-visual-regression.md`. Brief pointers here:

**jest-axe for RTL:**
```tsx
import { axe, toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

it('has no a11y violations', async () => {
  const { container } = render(<LoginForm />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

**Playwright + axe:**
```ts
import AxeBuilder from '@axe-core/playwright';

test('checkout page has no a11y violations', async ({ page }) => {
  await page.goto('/checkout');
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});
```

---

## CI: Parallelization, Flaky Tests, and Test Selection

### Q: How do you structure a testing pipeline that does not slow teams down?

**Parallelization:**
- Vitest: `pool: 'threads'`, `maxThreads: os.cpus().length`
- Playwright: `fullyParallel: true` with sharding across CI workers
- Jest: `--runInBand` for debugging only; use `--maxWorkers=50%` in CI

**Flaky test management:**
- Tag flaky tests: `test.skip` or `test.fixme` in Playwright, `test.todo` in Vitest
- Run the flaky suite nightly, not on every PR
- Track flakiness rate per test in your test reporter (Buildkite Flaky, Datadog CI)
- Do not retry on CI without a quarantine strategy — retries hide root causes

**Test selection:**
- Run only changed files on PR builds: Vitest's `--changed`, Jest's `--onlyChanged`
- Run the full suite on merge to main
- Use test impact analysis tools (Nx affected, Turborepo) in monorepos

---

## Senior Scenario

### Q: "This team has flaky e2e tests and slow CI — what do you do?"

This is a systems problem, not a tooling problem. The approach:

**Step 1 — Diagnose before fixing.** Instrument your CI pipeline. Which tests are flaky? How often? What is their average runtime? Do not guess — use data from your test reporter.

**Step 2 — Quarantine flaky tests immediately.** Move them to a nightly job or tag them `@flaky`. Stop letting them block PRs. This is the highest-leverage immediate action — it restores trust in the suite.

**Step 3 — Analyze the flakiness root causes.** Common causes: timing assertions (`waitForTimeout`), shared test state (no DB reset between tests), port conflicts in parallel runs, non-deterministic test order, external API calls not mocked.

**Step 4 — Shift coverage left.** For every e2e test covering something that could be covered by a RTL integration test, replace it. E2e tests should cover only what requires a full browser — routing, OAuth flows, file uploads, multi-tab scenarios.

**Step 5 — Speed up CI structurally.** Shard e2e across workers. Cache `node_modules` and build artifacts. Use test impact analysis to skip unrelated tests on PRs. Set a CI time budget and treat violations as regressions.

**Step 6 — Fix flaky tests one by one, in priority order.** Start with the tests that block the most PRs. Root cause each one — do not add retries as a fix.

> 💡 Senior insight: A flaky test suite is a trust problem. Engineers learn to ignore red CI runs. Once that happens, real failures get missed in production. Restoring trust — through quarantine, root cause analysis, and structural fixes — is more valuable than any individual test you could write.

---

## ⚡ Rapid-Fire

- **`getBy` vs `queryBy`**: `getBy` throws on missing; `queryBy` returns null — use it for asserting absence.
- **Why avoid `data-testid`?**: It adds no a11y signal and creates test coupling to markup details. Use role + name.
- **What is `screen`?**: RTL's bound query object that searches the full rendered document — preferred over destructuring from `render()`.
- **`beforeEach` vs `afterEach` for MSW?**: Use `afterEach(() => server.resetHandlers())` to avoid handler state leaking between tests.
- **How do you test a `useEffect` that runs on mount?**: Render the component, assert on the side effect's output (DOM change, mock call) — do not test the effect directly.
- **Vitest ESM vs Jest**: Jest requires `transform` config for ESM modules; Vitest handles them natively via Vite.
- **When to use `waitFor` vs `findBy`**: Use `findBy` when waiting for an element to appear; use `waitFor` when waiting for an assertion on an already-present element to become true.
- **What does `retry: false` in QueryClient do in tests?**: Prevents React Query from retrying failed requests, avoiding timeout-induced `act()` warnings.
- **Mutation score vs coverage**: Coverage = lines executed; mutation score = percentage of deliberate code mutations your tests catch. Mutation score is the stronger signal.
- **Playwright `trace`**: A ZIP file of screenshots, network logs, and DOM snapshots for a test run — invaluable for debugging CI flakiness locally.

---

## 🚩 Red Flags

- **"We aim for 100% coverage"** — indicates the team is gaming metrics rather than building confidence. Ask what their mutation score is.
- **Snapshot tests on every component** — teams that snapshot entire page renders have a suite that regenerates on every styling change and is reviewed by no one.
- **`jest.mock` on `axios` or `fetch`** — tests the mock, not the integration. Should be using MSW.
- **No integration tests, only unit tests** — heavily mocked unit tests prove each piece works in isolation, not that they work together. The integration layer is where most real bugs live.
- **Retries in CI as a permanent fix** — retries hide flakiness root causes. A test with `retries: 3` is a test that sometimes fails, always passing eventually.
- **`act()` wrappers everywhere without explanation** — indicates suppression of a symptom rather than diagnosis of async timing issues.
- **E2e tests for every feature** — slow CI, high flakiness, difficult debugging. E2e should cover critical journeys, not feature parity.
- **Testing implementation: asserting on `useState` values or private methods** — these tests break on every refactor and provide no confidence about user-facing behavior.
- **No test utilities / no custom render** — every test re-creates providers from scratch. Sign of no shared testing culture or standards.
- **"We don't have time to write tests"** — at senior/lead level, the correct response is "we don't have time not to." Untested code is technical debt that accumulates interest until a production incident.
