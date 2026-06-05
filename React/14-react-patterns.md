# React Component Design Patterns

Senior interviews revisit patterns because knowing *when not to use* a pattern — and articulating *why it was superseded* — signals architectural maturity. Pattern questions probe whether you can reason about trade-offs (coupling, flexibility, DX, testability) rather than just recite APIs. Expect questions that force you to compare approaches and defend a choice in context.

---

## Higher-Order Components (HOC)

### What is an HOC and when should you still reach for one?

An HOC is a function that takes a component and returns a new component with augmented behavior. The pattern predates hooks and solved cross-cutting concerns (auth gating, error boundaries, analytics) before logic could live outside components.

**HOC still makes sense for:**
- `withErrorBoundary` — error boundaries *must* be class components; an HOC wraps cleanly
- Auth / permission gating at the route level where a wrapper-component model fits the router API
- Third-party HOC APIs (Redux `connect`, `React.memo`, `React.forwardRef`) you compose, not author

```tsx
// withErrorBoundary — legitimate modern HOC
import { ComponentType, Component, ErrorInfo } from "react";

interface ErrorBoundaryState { hasError: boolean; error: Error | null }

class ErrorBoundaryInner extends Component<
  { fallback: ComponentType<{ error: Error }>; children: React.ReactNode },
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Boundary caught:", error, info.componentStack);
  }

  render() {
    if (this.state.hasError && this.state.error) {
      const Fallback = this.props.fallback;
      return <Fallback error={this.state.error} />;
    }
    return this.props.children;
  }
}

function withErrorBoundary<P extends object>(
  WrappedComponent: ComponentType<P>,
  FallbackComponent: ComponentType<{ error: Error }>
) {
  const DisplayName = WrappedComponent.displayName ?? WrappedComponent.name ?? "Component";

  function WithErrorBoundary(props: P) {
    return (
      <ErrorBoundaryInner fallback={FallbackComponent}>
        <WrappedComponent {...props} />
      </ErrorBoundaryInner>
    );
  }

  // ⚠️ Gotcha: always set displayName or DevTools shows "WithErrorBoundary" everywhere
  WithErrorBoundary.displayName = `withErrorBoundary(${DisplayName})`;
  return WithErrorBoundary;
}
```

**Why hooks largely replaced HOCs:**
- HOCs inject props, creating *prop collision* when two HOCs add the same prop name
- Refs don't pass through without explicit `React.forwardRef` wrapping
- Wrapping multiple HOCs creates an indirection stack in DevTools
- Hooks colocate the same logic without adding a component layer

> 💡 Senior insight: The question isn't "HOCs vs hooks" — it's "does this concern naturally live at the component boundary or inside render logic?" Error boundaries and third-party wrappers stay as HOCs. Data fetching, subscriptions, and derived state move to hooks.

**Follow-ups they'll ask:**
- How do you handle TypeScript generics in an HOC without losing the wrapped component's prop types?
- How do you forward refs through an HOC?
- Name a production HOC you'd author today vs one you'd rewrite as a hook.

---

## Render Props

### Explain the render prop pattern. Why did it fall out of favor, and where does it still win?

A render prop is a prop (often `children`) whose value is a function the component calls with its internal state, giving the caller control over rendering.

```tsx
// Classic render prop
interface MousePosition { x: number; y: number }

function MouseTracker({ children }: { children: (pos: MousePosition) => React.ReactNode }) {
  const [pos, setPos] = React.useState<MousePosition>({ x: 0, y: 0 });
  return (
    <div onMouseMove={e => setPos({ x: e.clientX, y: e.clientY })}>
      {children(pos)}
    </div>
  );
}

// Usage — fine for one level, painful when nested
<MouseTracker>
  {({ x, y }) => <p>Mouse: {x}, {y}</p>}
</MouseTracker>
```

**Why it caused wrapper hell:** three nested render props produce deeply indented, hard-to-read JSX sometimes called "callback hell on JSX." Each layer re-renders independently, making performance analysis non-obvious.

**Where render props still win — headless/flexible UI:**
```tsx
// Render prop shines when the consumer owns layout entirely
<Combobox
  items={results}
  onSelect={handleSelect}
  renderItem={({ item, isHighlighted }) => (
    <li className={isHighlighted ? "bg-blue-100" : ""}>{item.label}</li>
  )}
  renderEmpty={() => <li>No results</li>}
/>
```

> 💡 Senior insight: Headless UI libraries (Radix, React Aria) often expose render props / function-as-children at leaf nodes for this exact flexibility. Hooks replaced render props for *logic reuse*; render props remain relevant for *UI customization points*.

**Follow-ups they'll ask:**
- How does a render prop differ from a slot prop?
- Can a render prop component be memoized effectively?

---

## Custom Hooks Pattern

### When do you extract logic into a custom hook, and what should it return?

Custom hooks are the *default* answer for logic reuse in modern React. See `04-hooks.md` for rules and deep-dive; here the focus is the pattern itself.

**Extract to a hook when:** the same stateful logic appears in two or more components, or a single component's logic is complex enough to benefit from isolation and independent testing.

**Return shape — tuple vs object:**
```tsx
// Tuple: great for rename-at-callsite (like useState)
function useToggle(initial = false): [boolean, () => void, () => void] {
  const [on, setOn] = React.useState(initial);
  return [on, () => setOn(true), () => setOn(false)];
}
const [isOpen, open, close] = useToggle();

// Object: better when there are 3+ return values or they're rarely all used
function usePagination({ total, pageSize }: { total: number; pageSize: number }) {
  const [page, setPage] = React.useState(1);
  const totalPages = Math.ceil(total / pageSize);
  return {
    page,
    totalPages,
    isFirst: page === 1,
    isLast: page === totalPages,
    next: () => setPage(p => Math.min(p + 1, totalPages)),
    prev: () => setPage(p => Math.max(p - 1, 1)),
    goTo: setPage,
  };
}
```

**Composing hooks:**
```tsx
// Hooks compose naturally — no wrapper components needed
function useUserSearch(query: string) {
  const debouncedQuery = useDebounce(query, 300);       // reusable
  const { data, isLoading } = useQuery(                 // TanStack Query
    ["users", debouncedQuery],
    () => fetchUsers(debouncedQuery),
    { enabled: debouncedQuery.length > 1 }
  );
  return { users: data ?? [], isLoading };
}
```

> 💡 Senior insight: A hook that returns too many things is doing too much. Apply the single-responsibility principle: `useFormField` handles one field; `useForm` composes multiple `useFormField` calls.

**Follow-ups they'll ask:**
- How do you test a custom hook in isolation?
- When would you choose a hook over a context-based solution?

---

## Compound Components

### How do compound components share state, and what's the difference between the old and modern approach?

Compound components let related components communicate implicitly, giving consumers flexible composition without prop drilling.

**Old approach — React.Children + cloneElement:**
```tsx
// Fragile: breaks with fragments, maps, or conditional wrapping
function Tabs({ children, defaultTab = 0 }) {
  const [active, setActive] = React.useState(defaultTab);
  return React.Children.map(children, (child, i) =>
    React.cloneElement(child as React.ReactElement, { active: active === i, onSelect: () => setActive(i) })
  );
}
```
⚠️ Gotcha: `React.Children.map` flattens one level only and breaks if children are conditionally rendered inside fragments.

**Modern approach — Context:**
```tsx
interface TabsContextValue {
  activeIndex: number;
  setActiveIndex: (i: number) => void;
}
const TabsContext = React.createContext<TabsContextValue | null>(null);

function useTabs() {
  const ctx = React.useContext(TabsContext);
  if (!ctx) throw new Error("useTabs must be used inside <Tabs>");
  return ctx;
}

function Tabs({ children, defaultIndex = 0 }: { children: React.ReactNode; defaultIndex?: number }) {
  const [activeIndex, setActiveIndex] = React.useState(defaultIndex);
  return (
    <TabsContext.Provider value={{ activeIndex, setActiveIndex }}>
      <div role="tablist">{children}</div>
    </TabsContext.Provider>
  );
}

function Tab({ index, children }: { index: number; children: React.ReactNode }) {
  const { activeIndex, setActiveIndex } = useTabs();
  return (
    <button
      role="tab"
      aria-selected={activeIndex === index}
      onClick={() => setActiveIndex(index)}
    >
      {children}
    </button>
  );
}

function TabPanel({ index, children }: { index: number; children: React.ReactNode }) {
  const { activeIndex } = useTabs();
  return activeIndex === index ? <div role="tabpanel">{children}</div> : null;
}

Tabs.Tab = Tab;
Tabs.Panel = TabPanel;
```

**Controlled compound component** — lift state out by accepting `value` + `onChange`:
```tsx
<Tabs value={activeTab} onChange={setActiveTab}>
  <Tabs.Tab index={0}>Overview</Tabs.Tab>
  <Tabs.Tab index={1}>Details</Tabs.Tab>
  <Tabs.Panel index={0}><Overview /></Tabs.Panel>
  <Tabs.Panel index={1}><Details /></Tabs.Panel>
</Tabs>
```

> 💡 Senior insight: Compound components shine for design-system primitives where the consumer needs to control structure but not state wiring. The context-based approach scales to arbitrary nesting depth and conditional children.

**Follow-ups they'll ask:**
- How do you type the static properties (`Tabs.Tab`) in TypeScript?
- How do you handle the controlled/uncontrolled duality without duplicating logic?

---

## Provider Pattern

### How do you manage provider composition and avoid "provider hell"?

The provider pattern uses React Context for dependency injection — theme, auth, i18n, feature flags.

**Provider hell — the problem:**
```tsx
// Real codebases drift here quickly
<AuthProvider>
  <ThemeProvider>
    <FeatureFlagProvider>
      <I18nProvider>
        <QueryClientProvider client={queryClient}>
          <App />
        </QueryClientProvider>
      </I18nProvider>
    </FeatureFlagProvider>
  </ThemeProvider>
</AuthProvider>
```

**Solution 1 — compose providers into one component:**
```tsx
const providers: Array<React.ComponentType<{ children: React.ReactNode }>> = [
  AuthProvider,
  ThemeProvider,
  FeatureFlagProvider,
  I18nProvider,
  ({ children }) => <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>,
];

function AppProviders({ children }: { children: React.ReactNode }) {
  return providers.reduceRight(
    (acc, Provider) => <Provider>{acc}</Provider>,
    children
  );
}
```

**Solution 2 — colocate providers near their consumers** (not all at root). Feature-scoped context (e.g., a wizard's step state) belongs at the feature boundary, not the app root.

> 💡 Senior insight: Every context re-renders all consumers when its value reference changes. Split contexts by update frequency: a `ThemeContext` (rare updates) should never be in the same provider as a `NotificationContext` (frequent). Use `useMemo` on the value object or split state into separate contexts.

**Follow-ups they'll ask:**
- How do you prevent unnecessary re-renders from context value changes?
- How do you test components that depend on multiple providers?

---

## Container / Presentational (Smart / Dumb)

### Is the container/presentational split still valid?

Historically: a "container" component fetches data and holds state; a "presentational" component only renders props. Dan Abramov introduced this and later walked it back — hooks obsolete the distinction because logic now lives *in* the component without a wrapper class.

**What replaced it:**
```tsx
// Before hooks: UserContainer fetched, UserCard rendered
// After hooks: colocate the logic
function UserCard({ userId }: { userId: string }) {
  const { user, isLoading } = useUser(userId); // hook handles fetching
  if (isLoading) return <Skeleton />;
  return <article>{user.name}</article>;
}
```

**Where the split still has value:** when a presentational component needs to be *independently testable and Storybook-documented* without network calls. In that case, the split is organizational, not architectural — you author a pure `UserCardView` and a thin `UserCard` that wires the hook.

> 💡 Senior insight: The real lesson from Abramov's retraction isn't "never separate concerns" — it's "don't let a pattern become a rule. Separate when it adds testability or reuse, not as a reflex."

**Follow-ups they'll ask:**
- How does this pattern interact with server components in Next.js App Router?

---

## Controlled vs Uncontrolled & Advanced Control Patterns

### What is the "control props" pattern and when do you implement the state reducer pattern?

**Controlled vs uncontrolled as an API decision:** when building a reusable component, decide early whether it owns its state (uncontrolled) or delegates it (controlled). Expose both via the same interface using the "control props" pattern.

```tsx
interface SelectProps {
  // Controlled
  value?: string;
  onChange?: (value: string) => void;
  // Uncontrolled
  defaultValue?: string;
}

function Select({ value, onChange, defaultValue }: SelectProps) {
  const [internalValue, setInternalValue] = React.useState(defaultValue ?? "");
  const isControlled = value !== undefined;
  const current = isControlled ? value : internalValue;

  function handleChange(next: string) {
    if (!isControlled) setInternalValue(next);
    onChange?.(next);
  }
  // ...
}
```

⚠️ Gotcha: switching from uncontrolled to controlled mid-lifecycle (passing `undefined` then a value) triggers a React warning and unexpected state. Guard with `useRef` to detect the transition if needed.

**State reducer pattern (Kent C. Dodds):** invert control over *internal state transitions* by accepting a reducer from the consumer.

```tsx
type ToggleAction = { type: "toggle" } | { type: "reset" };
type ToggleState = { on: boolean };

function defaultReducer(state: ToggleState, action: ToggleAction): ToggleState {
  switch (action.type) {
    case "toggle": return { on: !state.on };
    case "reset": return { on: false };
    default: return state;
  }
}

function useToggle({
  reducer = defaultReducer,
}: {
  reducer?: (state: ToggleState, action: ToggleAction) => ToggleState;
} = {}) {
  const [state, dispatch] = React.useReducer(reducer, { on: false });
  return { ...state, toggle: () => dispatch({ type: "toggle" }) };
}

// Consumer: limit toggles to 3
const { on, toggle } = useToggle({
  reducer(state, action) {
    if (action.type === "toggle" && toggleCount >= 3) return state; // block
    return defaultReducer(state, action);
  },
});
```

**Prop getters:** instead of forwarding every event handler prop, expose a `getToggleProps()` that merges caller props with internal handlers — the pattern Downshift popularized.

> 💡 Senior insight: The state reducer pattern is the most powerful inversion-of-control technique for reusable components. It lets the consumer customize behavior for any action type without forking the component.

**Follow-ups they'll ask:**
- How do you prevent breaking changes when adding new action types to a state reducer?
- Distinguish "control props" from "fully controlled." When is the uncontrolled default the better API?

---

## Slots / Composition Patterns

### How do you implement slots in React, and why does children-as-content matter for performance?

React's composition model uses props to pass JSX subtrees — the equivalent of named slots from Web Components or Vue.

```tsx
interface CardProps {
  header: React.ReactNode;   // named slot
  footer?: React.ReactNode;
  children: React.ReactNode; // default slot
}

function Card({ header, footer, children }: CardProps) {
  return (
    <div className="card">
      <div className="card__header">{header}</div>
      <div className="card__body">{children}</div>
      {footer && <div className="card__footer">{footer}</div>}
    </div>
  );
}
```

**Performance — children as content:** when you pass JSX as `children` (or any prop), the *parent* creates the element; the child component just places it. If the parent doesn't re-render, the children prop reference is stable. This is the basis of the `children` trick for avoiding context-triggered re-renders — see `07-rendering.md` for the full analysis.

> 💡 Senior insight: Named slot props (`header`, `footer`) beat render props when the slot has no dynamic data flowing from the parent component. Reach for render props / function slots only when the parent needs to pass data *into* the slot's render function.

---

## Headless UI Pattern

### What is headless UI and why has it become the dominant library pattern?

A headless component provides all behavior, state management, and accessibility — but zero styling. The consumer owns the markup and CSS entirely.

**Examples:** React Aria, Radix UI Primitives, Headless UI (Tailwind Labs), TanStack Virtual, Downshift.

**Why headless won:**
- Design systems vary; behavior and a11y don't — splitting them lets teams own visuals without forking logic
- Accessibility is hard (focus management, ARIA attributes, keyboard events); centralize it once in the headless layer
- Styled wrappers composed from headless primitives are cheaper to maintain than styled-from-scratch components

```tsx
// Radix usage — behavior + a11y from Radix, styling from Tailwind
import * as Dialog from "@radix-ui/react-dialog";

function ConfirmDialog({ onConfirm }: { onConfirm: () => void }) {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <button className="btn-danger">Delete</button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white p-6 rounded-lg shadow-xl">
          <Dialog.Title>Confirm deletion</Dialog.Title>
          <Dialog.Description>This action cannot be undone.</Dialog.Description>
          <Dialog.Close asChild>
            <button onClick={onConfirm} className="btn-primary">Confirm</button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

> 💡 Senior insight: When evaluating a UI library for a design system, prefer headless primitives over fully styled component libraries. Full-style libraries (MUI, Chakra) trade flexibility for speed; headless libraries trade speed for long-term adaptability. At senior/lead level, expect to articulate this trade-off with timeline and team constraints in mind.

**Follow-ups they'll ask:**
- How does React Aria differ from Radix in its accessibility philosophy?
- How do you version-control a design system built on headless primitives?

---

## State Machines for Component Logic

### When does XState (or useReducer) become the right tool for component state?

When a component has more than 3-4 booleans that interact (`isLoading`, `isError`, `isSuccess`, `isRetrying`) you're encoding a state machine informally — and bugs emerge from impossible states.

```tsx
// Impossible state: isLoading && isError simultaneously
// Finite state machine prevents this
type FetchState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: User }
  | { status: "error"; error: Error };
```

For component-level complexity, a typed `useReducer` with a discriminated union often suffices. For multi-step flows with side effects (wizards, checkout), XState's visual tooling and explicit transition map pays off. See `12-system-design.md` for the architectural angle.

---

## Polymorphic Components

### How do you implement the `as` prop pattern?

The `as` prop lets a component render as any HTML element or React component, preserving its behavior while delegating the element type to the consumer.

```tsx
// See 02-typescript.md for the full generic typing approach
type PolymorphicProps<T extends React.ElementType> = {
  as?: T;
} & React.ComponentPropsWithoutRef<T>;

function Text<T extends React.ElementType = "p">({ as, ...props }: PolymorphicProps<T>) {
  const Component = as ?? "p";
  return <Component {...props} />;
}

<Text as="h1" className="text-2xl">Heading</Text>
<Text as={Link} href="/home">Nav link</Text>
```

⚠️ Gotcha: the TypeScript inference gets complex fast with `ref` forwarding — see `02-typescript.md` for the `PolymorphicForwardRefComponent` pattern.

---

## Pattern Decision Guide

### "I need to share X — which pattern?"

| Need | Reach for |
|---|---|
| Reusable stateful / side-effect logic | Custom hook |
| Cross-cutting component wrapper (boundary, auth gate) | HOC |
| Flexible UI structure with shared implicit state | Compound component |
| Consumer controls their own markup entirely | Headless component / render prop |
| App-wide dependency injection (theme, auth, i18n) | Provider / Context |
| Library-quality behavior + a11y, consumer owns styling | Headless primitive (Radix, React Aria) |
| Component that lets consumer override state transitions | State reducer pattern |
| Named layout regions with no data flow into them | Slot props (`header`, `footer`) |
| Infer element type from consumer | Polymorphic `as` prop |
| Complex multi-step flow with impossible-state prevention | State machine (useReducer / XState) |

---

## ⚡ Rapid-Fire

1. An HOC wraps a component; a hook wraps logic — one adds a component layer, one does not.
2. `displayName` on HOCs is mandatory; without it DevTools shows stacked anonymous wrappers.
3. `React.Children.map` breaks on fragments — Context is the correct compound-component approach today.
4. Render props are still valid when the consumer needs to own the markup of a specific slot.
5. The state reducer pattern inverts control over *how* state transitions happen, not just *when*.
6. Control props require you to detect controlled vs uncontrolled mode — never toggle between them.
7. Provider context values should be memoized or split by update frequency to prevent cascade re-renders.
8. Headless UI separates behavior/a11y from styling — the right trade for design-system longevity.
9. `children` as a prop is stable across parent renders if the parent doesn't re-render — use it for perf.
10. The container/presentational split is organizational choice, not architectural requirement, post-hooks.
11. Custom hooks should follow single-responsibility — one concern per hook, compose upward.
12. Tuple returns favor rename-ability; object returns favor selective destructuring.
13. `as` / polymorphic props are a consumer convenience, not a styling system — don't overload them.
14. Provider hell is solved by co-locating providers with their feature, not stacking all at root.
15. Compound components with Context support arbitrary nesting depth; `cloneElement` does not.
16. A discriminated union for state (`{ status: "loading" | "error" | "success" }`) prevents impossible states better than multiple booleans.
17. Prop getters (e.g., `getToggleProps`) merge consumer event handlers with internal ones — always call-through, never clobber.
18. `React.memo` is itself an HOC; wrapping it with another HOC requires careful ref and displayName handling.
19. Headless libraries own ARIA and keyboard behavior — prefer them over hand-rolling for accessibility compliance.
20. The best pattern is the one your team can read, extend, and delete without a comment explaining why it exists.

---

## 🚩 Red Flags

- **Using HOCs for logic reuse in new code** — signals unfamiliarity with hooks; articulate the boundary.
- **`React.cloneElement` in compound components** — shows the pattern but not the modern implementation.
- **All providers at the app root regardless of scope** — causes unnecessary re-renders and tight coupling.
- **Booleans for mutually exclusive states** — `isLoading && !isError` is a bug waiting to happen; use discriminated unions.
- **Not exposing both controlled and uncontrolled modes** in a reusable input component — forces consumers into one model.
- **Reaching for render props when a hook suffices** — over-engineering; can't explain the trade-off.
- **No `displayName` on HOCs or context** — dev experience and debuggability oversight at senior level.
- **Building a fully styled component library for a new design system** — headless + token layer is almost always the better investment at scale.
- **Ignoring `useMemo` on context value objects** — creates a re-render storm for all consumers on every parent render.
- **State reducer pattern without a default case that calls the original reducer** — breaks future action types and violates open/closed principle.
