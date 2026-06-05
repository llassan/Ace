# TypeScript for Senior React Engineers

TypeScript at a senior level is not about knowing syntax — it is about modeling domain constraints at compile time, catching entire categories of bugs before they ship, and writing types that serve as executable documentation. Senior/lead interviews probe whether you reason about the type system structurally, understand its unsoundness edges, and can make principled trade-offs between type safety and developer ergonomics.

---

## Structural Typing & Nominal Safety

### H3 — Why does TypeScript's structural typing surprise people, and when does it become a footgun?

**Mental model:** TypeScript types are *shapes*, not names. If two types share the same shape, they are assignable to each other — the type name is irrelevant. This is intentional for JavaScript interop but creates subtle correctness bugs.

```ts
type USD = number;
type EUR = number;

function charge(amount: USD) { /* ... */ }

const price: EUR = 9.99;
charge(price); // Compiles. No error. Wrong currency.
```

The type system cannot distinguish `USD` from `EUR` because they are aliases for the same primitive shape.

**Trade-off:** Structural typing gives you duck-typing flexibility and easy interop with third-party code, but you lose the nominal safety that domain modeling needs.

**Branded / opaque types for nominal-ish safety:**

```ts
type Brand<T, B extends string> = T & { readonly __brand: B };

type USD = Brand<number, "USD">;
type EUR = Brand<number, "EUR">;

// "constructor" that asserts the brand
const usd = (n: number): USD => n as USD;
const eur = (n: number): EUR => n as EUR;

function charge(amount: USD): void { /* ... */ }

const price = eur(9.99);
charge(price);         // Error: EUR is not assignable to USD
charge(usd(9.99));    // OK
```

> 💡 Senior insight: Branded types cost zero bytes at runtime (erased) but encode invariants the type system enforces at every call site. Use them for IDs (UserId, OrderId), units, validated strings (EmailAddress), and sanitized inputs.

⚠️ Gotcha: You still need a runtime validation step to *enter* the branded world safely. The brand cast `as USD` is an assertion — if you cast incorrectly, you have unsoundness. Pair with Zod schemas (see Async/API section).

**Follow-ups they'll ask:**
- How is a branded type different from a class with a private field?
- Can you achieve nominal typing with unique symbols? (Yes — `declare const __brand: unique symbol`)
- What are the ergonomic downsides of branding primitives in large codebases?

---

## `type` vs `interface`

### H3 — When do you reach for `interface` vs `type`, and is there a real performance difference?

**Mental model:** Both describe object shapes. The practical differences come down to three things: declaration merging, expressiveness, and tooling display.

| Capability | `interface` | `type` |
|---|---|---|
| Declaration merging | Yes | No |
| Extends other shapes | `extends` | `&` intersection |
| Union / conditional / mapped | No | Yes |
| Recursive self-reference | Easier historically | Works fine in modern TS |
| Error messages | Often cleaner ("Object with...") | Can show full expansion |

```ts
// Declaration merging — useful for module augmentation
interface Window {
  analytics: Analytics;
}
// A second interface Window declaration *merges*, not replaces.

// type cannot merge:
type Config = { debug: boolean };
type Config = { verbose: boolean }; // Error: Duplicate identifier
```

```ts
// type is required for unions, conditionals, mapped types
type StringOrNumber = string | number;
type Result<T> = { ok: true; data: T } | { ok: false; error: string };
type Readonly2<T> = { readonly [K in keyof T]: T[K] };
```

**The "performance myth":** TypeScript compiler docs note interfaces are cached as named types, while complex type aliases may be re-evaluated. In practice, this only matters at extreme scale (tens of thousands of intersections). Use whichever is cleaner; do not pre-optimize.

> 💡 Senior insight: Use `interface` for public API contracts and library typings (merging lets consumers augment). Use `type` for everything else — unions, mapped types, utility compositions. Never use one rule exclusively.

⚠️ Gotcha: Extending an interface with an incompatible property raises an error at the `extends` clause. Intersecting the same types with `&` silently produces `never` for the conflicting property — both are "errors," but `&` hides it until you use the type.

**Follow-ups they'll ask:**
- When would you use declaration merging intentionally in a React app?
- How do you augment third-party module types?

---

## Generics

### H3 — Walk me through how TypeScript infers generic types, and how you control inference with constraints and defaults.

**Mental model:** Generics are type-level functions. TypeScript infers the type argument from usage context. Constraints narrow what shapes are acceptable; defaults provide fallbacks.

```ts
// Basic inference — T inferred as string[]
function first<T>(arr: T[]): T | undefined {
  return arr[0];
}
const x = first(["a", "b"]); // x: string | undefined

// Constraint: T must have a .length property
function longest<T extends { length: number }>(a: T, b: T): T {
  return a.length >= b.length ? a : b;
}

// Default: allows omitting the type argument
type ApiResponse<T = unknown> = { data: T; status: number };
const raw: ApiResponse = { data: {}, status: 200 }; // T defaults to unknown
```

**Generic React components (modern — no `function` + comma hack needed with tsx):**

```tsx
type ListProps<T> = {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  keyExtractor: (item: T) => string;
};

function List<T>({ items, renderItem, keyExtractor }: ListProps<T>) {
  return (
    <ul>
      {items.map((item, i) => (
        <li key={keyExtractor(item)}>{renderItem(item, i)}</li>
      ))}
    </ul>
  );
}

// Usage — T inferred as { id: string; name: string }
<List
  items={users}
  keyExtractor={(u) => u.id}
  renderItem={(u) => <span>{u.name}</span>}
/>
```

> 💡 Senior insight: Prefer inferring generics from usage rather than requiring callers to annotate. If you find yourself writing `<List<User> items={...}>`, the generic probably needs better constraints or a different design.

⚠️ Gotcha: In `.tsx` files, `<T>` is ambiguous with JSX. Use `<T,>` or `<T extends object>` to disambiguate.

**Follow-ups they'll ask:**
- What is the difference between `T extends string` and `T = string`?
- How do you type a function that accepts a class constructor generically?
- What is `infer` and how does it differ from a generic parameter?

---

## Narrowing & Discriminated Unions

### H3 — How do discriminated unions model async state, and why do interviewers love them?

**Mental model:** A discriminated union is a union of types that all share a common *literal* property (the discriminant). Narrowing on that property eliminates impossible states at the type level.

**The async state anti-pattern:**

```ts
// Bad: multiple booleans create 2^3 = 8 states, most invalid
type BadState = {
  isLoading: boolean;
  data: User | null;
  error: Error | null;
};
// isLoading=true AND data=User is representable but nonsensical
```

**Discriminated union — only valid states exist:**

```ts
type AsyncState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: Error };

function UserProfile({ state }: { state: AsyncState<User> }) {
  switch (state.status) {
    case "idle":    return <Placeholder />;
    case "loading": return <Spinner />;
    case "success": return <Profile user={state.data} />; // data: User — safe
    case "error":   return <ErrorBanner error={state.error} />;
  }
}
```

**Exhaustiveness check with `never`:**

```ts
function assertNever(x: never): never {
  throw new Error(`Unhandled case: ${JSON.stringify(x)}`);
}

switch (state.status) {
  case "idle": ...
  case "loading": ...
  case "success": ...
  case "error": ...
  default: assertNever(state); // Error if a new status variant is added and not handled
}
```

**Type guards:**

```ts
// User-defined type guard
function isError(state: AsyncState<unknown>): state is { status: "error"; error: Error } {
  return state.status === "error";
}

// in narrowing
function processEvent(event: MouseEvent | KeyboardEvent) {
  if ("key" in event) {
    console.log(event.key); // event: KeyboardEvent
  }
}

// instanceof narrowing
function handle(value: Date | string) {
  if (value instanceof Date) {
    return value.toISOString(); // value: Date
  }
  return value.toUpperCase(); // value: string
}
```

> 💡 Senior insight: Discriminated unions + exhaustiveness checks turn "we forgot to handle the new case" from a runtime bug into a compile-time error. This is one of the highest-leverage patterns in TypeScript.

⚠️ Gotcha: Narrowing only works within the same scope. If you pass `state` into another function, the narrowed type does not travel with it — the callee sees the full union unless you use a type guard return type.

**Follow-ups they'll ask:**
- How do you narrow a `union` when the discriminant is not a string literal?
- What is the difference between `is` predicates and `asserts` predicates?
- How does `never` behave in union positions vs intersection positions?

---

## Utility Types Deep Dive

### H3 — Which utility types do you use most and can you implement a few from scratch?

**The essential toolkit:**

```ts
Partial<T>     // all props optional
Required<T>    // all props required
Readonly<T>    // all props readonly
Pick<T, K>     // keep only listed keys
Omit<T, K>     // exclude listed keys
Record<K, V>   // object with keys K and values V
ReturnType<F>  // return type of a function type
Parameters<F>  // tuple of parameter types
Awaited<T>     // unwrap Promise<T> recursively
NonNullable<T> // exclude null | undefined
```

**Build them from scratch (what interviews want):**

```ts
// Partial
type MyPartial<T> = { [K in keyof T]?: T[K] };

// Required
type MyRequired<T> = { [K in keyof T]-?: T[K] };
// -? removes optional modifier

// Readonly
type MyReadonly<T> = { readonly [K in keyof T]: T[K] };

// Pick
type MyPick<T, K extends keyof T> = { [P in K]: T[P] };

// Omit
type MyOmit<T, K extends keyof T> = MyPick<T, Exclude<keyof T, K>>;

// Record
type MyRecord<K extends keyof any, V> = { [P in K]: V };

// ReturnType
type MyReturnType<F extends (...args: any) => any> =
  F extends (...args: any) => infer R ? R : never;

// Parameters
type MyParameters<F extends (...args: any) => any> =
  F extends (...args: infer P) => any ? P : never;

// Awaited (simplified)
type MyAwaited<T> = T extends Promise<infer U> ? MyAwaited<U> : T;
```

> 💡 Senior insight: Knowing how to implement these demonstrates you understand mapped types, conditional types, and `infer` — the three pillars of advanced TypeScript. Interviewers care more about your reasoning than memorized implementations.

**Follow-ups they'll ask:**
- How does `Exclude<T, U>` differ from `Omit<T, K>`?
- What does `-readonly` do in a mapped type?
- When would you use `Parameters` in a real codebase?

---

## Conditional Types, `infer`, Mapped Types, Template Literals

### H3 — Explain conditional types and `infer` with a practical example.

**Mental model:** Conditional types are ternary expressions at the type level. `infer` introduces a type variable that TypeScript resolves by pattern matching.

```ts
// Basic conditional type
type IsArray<T> = T extends any[] ? true : false;
type A = IsArray<string[]>; // true
type B = IsArray<string>;   // false

// infer to extract inner type
type ElementType<T> = T extends (infer E)[] ? E : never;
type C = ElementType<string[]>; // string
type D = ElementType<number>;   // never

// Unpacking a Promise chain
type DeepAwaited<T> = T extends Promise<infer U> ? DeepAwaited<U> : T;
type E = DeepAwaited<Promise<Promise<string>>>; // string

// Infer from function signature
type FirstArg<F> = F extends (first: infer A, ...rest: any[]) => any ? A : never;
type F2 = FirstArg<(name: string, age: number) => void>; // string
```

**Key remapping in mapped types:**

```ts
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

type User = { name: string; age: number };
type UserGetters = Getters<User>;
// { getName: () => string; getAge: () => number }
```

**Template literal types:**

```ts
type EventName<T extends string> = `on${Capitalize<T>}`;
type ClickHandler = EventName<"click">; // "onClick"

type CSSProperty = "margin" | "padding";
type CSSDirection = "Top" | "Right" | "Bottom" | "Left";
type LonghandCSS = `${CSSProperty}${CSSDirection}`;
// "marginTop" | "marginRight" | ... | "paddingLeft"
```

> 💡 Senior insight: Template literal types are powerful for generating event handler maps, REST endpoint strings, and CSS property unions without manual enumeration. They eliminate entire categories of typos in string-keyed APIs.

⚠️ Gotcha: Conditional types distribute over naked type parameters. `type ToArray<T> = T extends any ? T[] : never` — when called with `string | number`, produces `string[] | number[]`, not `(string | number)[]`. Wrap in a tuple `[T]` to prevent distribution.

---

## `unknown` vs `any` vs `never`

### H3 — When is each of `unknown`, `any`, and `never` correct?

**Mental model:**

| Type | Assignable from | Assignable to | Use case |
|---|---|---|---|
| `any` | everything | everything | Escape hatch — opt out of type checking |
| `unknown` | everything | only `unknown` / `any` | Safe top type — must narrow before use |
| `never` | nothing | everything | Bottom type — unreachable code, exhaustion |

```ts
// unknown — forces you to prove the type before using it
function parseJSON(raw: string): unknown {
  return JSON.parse(raw);
}
const result = parseJSON('{"id":1}');
result.id; // Error — Object is of type unknown
if (typeof result === "object" && result !== null && "id" in result) {
  (result as { id: number }).id; // OK after narrowing
}

// any — disables checking entirely
function dangerous(x: any) {
  x.whatever.you.want; // No error — but runtime may explode
}

// never — exhaustiveness, impossible branches
function fail(message: string): never {
  throw new Error(message); // never returns
}

type Shape = { kind: "circle" } | { kind: "square" };
function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle": return 0;
    case "square": return 0;
    default: return assertNever(shape); // shape: never — all cases handled
  }
}
```

> 💡 Senior insight: `any` is a bilateral escape; `unknown` is a unilateral receive — you accept anything but must prove before using. Prefer `unknown` for API boundaries, JSON parsing, and error catches. `never` in a union disappears; `never` in an intersection absorbs everything.

⚠️ Gotcha: `catch (e)` gives `e: unknown` in strict mode (correct). In older code you may see `e: any`. Always check before accessing `e.message`.

---

## `as const`, Const Type Params, `satisfies`

### H3 — Why does `satisfies` beat type annotation, and when do you use `as const`?

**`as const` — freeze to narrowest literal type:**

```ts
const directions = ["north", "south", "east", "west"] as const;
// readonly ["north", "south", "east", "west"]
type Direction = typeof directions[number]; // "north" | "south" | "east" | "west"

// Without as const:
const dirs = ["north", "south"]; // string[] — loses literal info
```

**`satisfies` — validate shape without widening:**

```ts
type Palette = { [key: string]: [number, number, number] | string };

// Annotation — loses specific type of each key
const p1: Palette = { red: [255, 0, 0], blue: "royalblue" };
p1.red;  // [number, number, number] | string — lost the tuple info

// satisfies — validates against Palette but preserves specific types
const p2 = {
  red: [255, 0, 0],
  blue: "royalblue",
} satisfies Palette;
p2.red;  // [number, number, number] — kept!
p2.blue; // string — kept!
p2.red.toUpperCase(); // Error — tuple has no toUpperCase
```

**Const type parameters (TS 5.0+):**

```ts
// Without const — T inferred as string[]
function identity<T>(value: T): T { return value; }
identity(["a", "b"]); // T = string[]

// With const — T inferred as readonly ["a", "b"]
function identityConst<const T>(value: T): T { return value; }
identityConst(["a", "b"]); // T = readonly ["a", "b"]
```

> 💡 Senior insight: Use `satisfies` when you want the compiler to check your object against a type but need to retain the inferred literal/tuple types for downstream consumers. Classic use case: route config objects, theme tokens, icon registries.

---

## Typing React

### H3 — How do you type a polymorphic `as` prop component correctly?

**Mental model:** A polymorphic component renders as different HTML elements or components. The prop types must adapt to whichever element is chosen.

```tsx
import React from "react";

type AsProp<C extends React.ElementType> = { as?: C };

type PropsToOmit<C extends React.ElementType, P> = keyof (AsProp<C> & P);

type PolymorphicComponentProps<
  C extends React.ElementType,
  Props = {}
> = React.PropsWithChildren<Props & AsProp<C>> &
  Omit<React.ComponentPropsWithoutRef<C>, PropsToOmit<C, Props>>;

// Usage
type TextProps = { size?: "sm" | "md" | "lg" };

function Text<C extends React.ElementType = "span">({
  as,
  size = "md",
  children,
  ...rest
}: PolymorphicComponentProps<C, TextProps>) {
  const Component = as ?? "span";
  return <Component className={`text-${size}`} {...rest}>{children}</Component>;
}

// Renders as <p>, href is invalid — correctly errors
<Text as="p" href="/foo">Hello</Text>

// Renders as <a>, href is valid
<Text as="a" href="/foo">Hello</Text>
```

**forwardRef with generics:**

```tsx
type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
};

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, ...props }, ref) => (
    <label>
      {label}
      <input ref={ref} {...props} />
    </label>
  )
);
```

**Typing custom hooks:**

```ts
// Return a tuple with const assertion for correct inference
function useToggle(initial: boolean): [boolean, () => void] {
  const [value, setValue] = React.useState(initial);
  const toggle = React.useCallback(() => setValue((v) => !v), []);
  return [value, toggle]; // Without annotation, inferred as (boolean | (() => void))[]
}
```

**Discriminated props for component variants:**

```tsx
type ButtonProps =
  | { variant: "primary"; onClick: () => void; href?: never }
  | { variant: "link"; href: string; onClick?: never };

function Button(props: ButtonProps) {
  if (props.variant === "link") {
    return <a href={props.href}>{/* ... */}</a>;
  }
  return <button onClick={props.onClick}>{/* ... */}</button>;
}
// <Button variant="link" onClick={...} /> — Error: onClick conflicts
```

**Typing context:**

```tsx
type AuthContext = { user: User; signOut: () => void };
const AuthCtx = React.createContext<AuthContext | null>(null);

function useAuth(): AuthContext {
  const ctx = React.useContext(AuthCtx);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx; // ctx: AuthContext — null eliminated
}
```

**Event types:**

```tsx
const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  setValue(e.target.value);
};
const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault();
};
const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
  if (e.key === "Enter" && e.shiftKey) submit();
};
```

> 💡 Senior insight: The polymorphic `as` pattern is a common senior interview question. Most candidates sketch it; few get the `Omit` + `PropsWithoutRef` combination right. The key insight is that the component's own props must shadow any conflicting native props.

⚠️ Gotcha: `React.FC` used to be popular but it implicitly typed `children` as optional (pre-React 18) and breaks generic components. Prefer plain function signatures with explicit `React.ReactNode` for children.

---

## Typing Async / API Layer

### H3 — Why don't TypeScript types guarantee runtime safety for API responses, and what is the correct pattern?

**Mental model:** TypeScript types are erased at compile time. A type assertion on a `fetch` response tells the compiler what you believe the shape is — it does not verify it. A malformed API response silently passes the type check and causes runtime errors.

```ts
// Unsafe — type assertion is a lie if the API changes
async function getUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`);
  return res.json() as User; // compiler believes you
}
```

**Correct pattern — Zod for runtime + compile-time safety:**

```ts
import { z } from "zod";

const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  role: z.enum(["admin", "viewer"]),
  createdAt: z.coerce.date(),
});

type User = z.infer<typeof UserSchema>; // derived from schema — single source of truth

async function getUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const raw: unknown = await res.json();
  return UserSchema.parse(raw); // throws ZodError if shape is wrong
}
```

**Typed fetch wrapper:**

```ts
async function apiFetch<T>(
  schema: z.ZodType<T>,
  input: RequestInfo,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(input, init);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return schema.parse(await res.json());
}

const user = await apiFetch(UserSchema, "/api/users/1");
// user: User — both runtime-validated and compile-time typed
```

> 💡 Senior insight: `z.infer<typeof Schema>` makes the Zod schema the single source of truth. If you annotate a separate `type User = { ... }`, you now have two places to update and can drift. Always derive the TS type from the schema.

⚠️ Gotcha: `z.parse` throws on failure; `z.safeParse` returns `{ success: boolean; data?: T; error?: ZodError }`. For UI error handling, `safeParse` is usually better — it lets you show validation errors instead of crashing.

---

## Variance: Covariance, Contravariance, Bivariance

### H3 — What is contravariance and why does it matter for function types?

**Mental model:**
- **Covariant** — you can use a subtype where a supertype is expected (return positions, read-only data). Safe to widen.
- **Contravariant** — you must use a supertype where a subtype is expected (function parameter positions). Callers control input; the function must handle everything the caller might pass.

```ts
class Animal { breathe() {} }
class Dog extends Animal { bark() {} }

// Covariant return type — OK
type Producer<T> = () => T;
const produceDog: Producer<Dog> = () => new Dog();
const produceAnimal: Producer<Animal> = produceDog; // OK — Dog is a subtype of Animal

// Contravariant parameter — Dog handler cannot stand in for Animal handler
type Consumer<T> = (t: T) => void;
const consumeAnimal: Consumer<Animal> = (a) => a.breathe();
const consumeDog: Consumer<Dog> = consumeAnimal; // OK — Animal handler can handle Dog (it has .breathe)
// const consumeAnimal2: Consumer<Animal> = consumeDog; // Error — Dog handler expects .bark()
```

**The `strictFunctionTypes` flag:**

Without `strictFunctionTypes`, TypeScript uses **bivariance** for method parameters — both `Consumer<Animal>` and `Consumer<Dog>` are assignable to each other. This is unsound but was the default for backward compat.

With `strictFunctionTypes` (enabled by `strict`), function-typed *properties* declared with `->` syntax are checked contravariantly. Methods declared with shorthand `method(arg: T)` still use bivariance (intentional — breaks too many patterns otherwise).

```ts
interface Processor {
  // method shorthand — bivariant (even with strictFunctionTypes)
  process(event: MouseEvent): void;
}

interface Processor2 {
  // property arrow — contravariant under strictFunctionTypes
  process: (event: MouseEvent) => void;
}
```

> 💡 Senior insight: The bivariance of method shorthands is a known unsoundness. If you need safe variance checking on callbacks, use the arrow property form in interfaces/types.

⚠️ Gotcha: Arrays in TypeScript are covariant (`Dog[]` is assignable to `Animal[]`), which is technically unsound. `const dogs: Dog[] = []; const animals: Animal[] = dogs; animals.push(new Animal());` — `dogs[0]` is now a non-Dog at runtime. TypeScript accepts this for pragmatism.

---

## tsconfig Essentials

### H3 — Which tsconfig flags does a senior engineer need to own, and what do they catch?

**Strict mode is a floor, not a ceiling:**

```jsonc
{
  "compilerOptions": {
    "strict": true,                    // enables all strict* flags
    "noUncheckedIndexedAccess": true,  // arr[0] is T | undefined, not T
    "noImplicitOverride": true,        // must use override keyword on class methods
    "exactOptionalPropertyTypes": true,// { x?: string } means x is string, not string|undefined
    "noPropertyAccessFromIndexSignature": true, // obj.key errors, must use obj["key"]
    "moduleResolution": "bundler",     // correct for Vite/esbuild projects
    "verbatimModuleSyntax": true,      // enforces type-only imports; prevents runtime leaks
    "isolatedModules": true,           // ensures each file can be transpiled independently
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"]
  }
}
```

**`noUncheckedIndexedAccess` — the one flag most teams should enable:**

```ts
const arr = [1, 2, 3];
const x = arr[0]; // With flag: number | undefined. Without: number
x.toFixed(2);     // Error — x might be undefined

const map: Record<string, User> = {};
const user = map["alice"]; // user: User | undefined
user.name; // Error — must check first
```

**Declaration files and ambient types:**

```ts
// global.d.ts — augment global scope
declare global {
  interface Window { __REDUX_DEVTOOLS_EXTENSION__?: () => any; }
}
export {}; // must be a module (has export)

// vite-env.d.ts — ambient imports
/// <reference types="vite/client" />
// Now import.meta.env.VITE_API_URL is typed

// Typing CSS modules
declare module "*.module.css" {
  const classes: Record<string, string>;
  export default classes;
}
```

> 💡 Senior insight: `noUncheckedIndexedAccess` alone would catch a meaningful percentage of real-world production bugs. Most teams skip it because it requires touching a lot of existing code. Enable it on new projects from day one.

⚠️ Gotcha: `verbatimModuleSyntax` requires `import type` for type-only imports. This prevents the bundler from emitting runtime imports for types, which can cause module resolution errors or unintended side effects.

---

## Common Type-Level Pitfalls

### H3 — What are the most dangerous type-level antipatterns in a senior React codebase?

**1. `any` leaks silently through inference:**

```ts
async function fetchData(): Promise<any> { // any infects everything downstream
  return fetch("/api").then(r => r.json());
}
const data = await fetchData(); // data: any
data.nonExistent.deeply.nested; // No error — type checking is off
```

Fix: return `unknown` and parse, or use a typed wrapper.

**2. Unsound type assertions (`as`) without validation:**

```ts
const user = response.data as User; // assertion, not check
user.email.toLowerCase(); // runtime crash if email is undefined
```

Fix: use Zod parse, or at minimum narrow with a type guard that actually checks.

**3. Index signature foot-guns:**

```ts
type UserMap = { [id: string]: User };
const users: UserMap = {};
const u = users["ghost"]; // u: User (without noUncheckedIndexedAccess)
u.name; // Runtime crash — u is undefined
```

Fix: enable `noUncheckedIndexedAccess`; or use `Map<string, User>` with explicit existence checks.

**4. `object` vs `Record<string, unknown>` vs `{}`:**

```ts
function process(x: object) { /* ... */ }
function process2(x: {}) { /* ... */ }
// {} accepts everything except null/undefined — primitives included!
process2(42); // No error — surprising

// Record<string, unknown> is what you usually want for "an object with string keys"
```

**5. Mutating inferred `const` type with `as`:**

```ts
const STATUS = { active: "active", inactive: "inactive" };
type Status = typeof STATUS[keyof typeof STATUS]; // string — not the literals!
// Fix:
const STATUS2 = { active: "active", inactive: "inactive" } as const;
type Status2 = typeof STATUS2[keyof typeof STATUS2]; // "active" | "inactive"
```

> 💡 Senior insight: The highest-leverage tsconfig+pattern combo: `strict + noUncheckedIndexedAccess + Zod at API boundaries + branded types for domain primitives`. This eliminates the most common classes of runtime bugs while keeping types expressive.

---

## ⚡ Rapid-Fire

1. **Structural vs nominal typing in one sentence?** TS checks shape, not name — two different types with the same shape are mutually assignable.
2. **When does `never` appear in a union?** It disappears — `string | never` = `string`.
3. **`unknown` vs `any` in a catch block?** `unknown` in strict mode — must narrow before accessing `.message`.
4. **What does `-?` do in a mapped type?** Removes the optional modifier, making properties required.
5. **Can `interface` express a union?** No — unions require `type`.
6. **What is declaration merging used for?** Module augmentation, extending third-party types (e.g., `Express.Request`).
7. **`satisfies` in one use case?** Validate an object against a type while retaining narrow literal types.
8. **`as const` vs `Object.freeze`?** `as const` is compile-time only; `freeze` is runtime. They compose.
9. **Why is `React.FC` discouraged?** Adds implicit `children`, breaks generic components, returns `JSX.Element` not `ReactNode`.
10. **`ReturnType` of an async function?** `ReturnType<typeof fn>` = `Promise<T>`. Use `Awaited<ReturnType<typeof fn>>` for the resolved type.
11. **What flag makes `arr[0]` return `T | undefined`?** `noUncheckedIndexedAccess`.
12. **Conditional types distribute over what?** Naked type parameters in union position.
13. **`[T] extends [U]` vs `T extends U`?** Tuple wrapper prevents distribution.
14. **`infer` can appear where?** Only in the `extends` clause of a conditional type.
15. **`exactOptionalPropertyTypes` changes what?** `{ x?: string }` no longer allows `x: undefined`; only `x: string` or the property absent.
16. **Method shorthand vs arrow property for variance?** Arrow property is contravariant under `strictFunctionTypes`; method shorthand is bivariant.
17. **Branded type runtime cost?** Zero — erased at compile time.
18. **Why prefer `z.infer` over a separate type definition?** Single source of truth — the schema is the type; no drift.
19. **`const` type parameter (TS 5.0) does what?** Infers the narrowest literal type for the argument without requiring `as const` at call sites.
20. **`isolatedModules` matters for what?** Ensures each file is independently transpilable — required by esbuild, Babel, SWC; catches `const enum` and namespace export issues.

---

## 🚩 Red Flags

- Uses `any` as a first resort rather than `unknown` or a proper type.
- Cannot explain why types do not equal runtime safety.
- Has never heard of discriminated unions or uses boolean flag combinations for state.
- Says "interfaces are always faster than types" without caveat or evidence.
- Cannot implement `Partial` or `Pick` from scratch — shows they use utilities without understanding them.
- Uses `as` assertions everywhere instead of narrowing or Zod parsing.
- Does not know what `strict` enables — treating it as a single monolithic flag without understanding the sub-flags.
- Conflates `{}` with "empty object" — does not know `{}` accepts all non-nullish values.
- Has never used `satisfies` and cannot articulate the difference from annotation.
- Thinks TypeScript prevents all runtime errors — does not understand the gap between structural type system and runtime behavior.
- Cannot explain variance in function types, and does not know `strictFunctionTypes` exists.
- Uses `React.FC` unconditionally in 2025.
- Has no runtime validation strategy at API boundaries.
