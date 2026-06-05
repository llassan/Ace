# Build Tools & Bundlers

Modern React apps ship through a pipeline that takes source code, resolves every import, applies transforms, and emits optimized artifacts browsers can execute. Understanding that pipeline — not just "Vite is fast" — is what separates senior engineers from people who can configure things when they work. This file covers the tools, how they compose, and how to reason about them under interview pressure.

> Cross-links: bundle-size **performance tactics** live in [07-performance.md]; barrel-file and monorepo patterns in [17-monorepo-nx.md]; security around source maps and env vars in [10-security.md].

---

## The Job of a Bundler

Before bundlers, JavaScript shipped as a pile of `<script>` tags with implicit global dependencies and load-order bugs. AMD (`require.js`) and then CommonJS (Node) gave us explicit dependency declarations, but browsers couldn't run them natively. Bundlers solved this: starting from an **entry point**, they walk every `import`/`require`, build a **dependency graph**, apply **transforms** (transpile JSX, strip types, downlevel syntax), and emit one or more output chunks the browser can load.

The four distinct operations teams often conflate:

| Operation | What it does | Tool examples |
|---|---|---|
| **Bundling** | Merge modules into chunks | Webpack, Rollup, esbuild |
| **Transpilation** | AST → lower-syntax AST | Babel, SWC, esbuild |
| **Polyfilling** | Inject missing runtime APIs | core-js, @babel/polyfill |
| **Minification** | Remove whitespace, mangle names | Terser, esbuild, SWC |

Conflating these is a common interview slip. Babel **transpiles** arrow functions; it does not bundle. esbuild **does** bundle and minify but performs **zero type-checking**.

---

## Webpack

### Q: Explain the Webpack build model. How does it differ from newer tools?

**Trade-off:** Webpack is the most powerful and most complex bundler. Its plugin-based everything-is-a-module philosophy can handle any asset, but building that universality requires traversing the full dependency graph **synchronously in JavaScript** on every start, which is intrinsically slow.

**Core concepts:**

```js
// webpack.config.js
module.exports = {
  entry: './src/index.tsx',          // graph root(s)
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: '[name].[contenthash].js',
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'babel-loader',          // or swc-loader for speed
        exclude: /node_modules/,
      },
      { test: /\.css$/, use: ['style-loader', 'css-loader'] },
    ],
  },
  plugins: [
    new HtmlWebpackPlugin({ template: './public/index.html' }),
    new MiniCssExtractPlugin({ filename: '[name].[contenthash].css' }),
  ],
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
      },
    },
  },
};
```

**Loaders** transform individual file types (run right-to-left in each `use` array). **Plugins** operate on the full compilation lifecycle. Everything flows through the **tapable** hook system — this is why Webpack can do things like moment locale stripping, bundle analysis, and federation that simpler tools cannot.

**SplitChunksPlugin** automatically deduplicates shared modules across chunks. Dynamic imports (`import('./HeavyChart')`) create async chunks that the runtime loads on demand.

**HMR** works by injecting a WebSocket client that receives module-replacement patches from the dev server and surgically swaps hot-boundary modules without a full reload. For React, `react-refresh` hooks into component boundaries.

> 💡 Senior insight: Webpack's persistent cache (`cache: { type: 'filesystem' }`) closes most of the cold-start gap with Vite on repeat builds. Teams staying on Webpack for ecosystem reasons should always have this enabled.

⚠️ Gotcha: Loader order is **right to left** within a `use` array. `['style-loader', 'css-loader', 'sass-loader']` runs sass → css → style. Getting this wrong produces cryptic errors.

**Follow-ups they'll ask:**
- When would you keep Webpack over Vite? (Module Federation, complex multi-target builds, deeply customized loaders, existing large codebase with working config, need for webpack-specific ecosystem plugins like `@module-federation`.)
- How do you analyze a slow Webpack build? (`speed-measure-webpack-plugin`, `--profile`, check for missed `exclude: /node_modules/` on heavy loaders.)

---

## Vite

### Q: How does Vite achieve fast dev startup? What actually runs in production?

**Trade-off:** Vite's dev/prod split is a deliberate architectural choice — maximum dev speed by not bundling at all, production correctness via Rollup's proven output. The split means dev and prod *can* behave differently; that's the known downside.

**Dev mode — native ESM + esbuild pre-bundling:**

1. Vite starts an HTTP server instantly — no bundle step.
2. The browser requests `main.tsx`; Vite transforms it on demand (esbuild) and serves it as ESM.
3. Imports cascade: the browser fetches each module as it discovers it.
4. **Pre-bundling** (esbuild, run once): CJS packages like `lodash` are converted to ESM and merged into a single file so the browser makes one request instead of thousands. Cached under `node_modules/.vite`.

**Production — Rollup:**

```ts
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
        },
      },
    },
    sourcemap: true,   // set false or 'hidden' for prod (see §Source Maps)
  },
});
```

**HMR speed:** Because modules are served individually, an HMR update only invalidates the changed file and its direct importers — not the whole graph. Compare to Webpack where large dependency sub-trees can be invalidated on a single change.

> 💡 Senior insight: The pre-bundling cache invalidates when deps change, but you can force it with `vite --force`. If a colleague reports "Vite is broken after `npm install`" this is often the fix.

⚠️ Gotcha: Packages that use dynamic `require()` or conditional exports incompatible with ESM can break Vite dev. Always check `optimizeDeps.include` as a workaround before filing a bug.

**Follow-ups they'll ask:**
- How do you handle environment-specific config in Vite? (`.env`, `.env.production`; only `VITE_` prefixed vars are exposed to client code.)
- Can Vite build a library? (Yes — `build.lib` mode uses Rollup directly.)

---

## Rollup

### Q: Why do library authors prefer Rollup?

**Trade-off:** Rollup produces the cleanest ESM output because it was designed for libraries first. It performs **scope hoisting** (inlining small modules into the caller's scope) rather than wrapping each module in a function closure like Webpack does. The result is smaller, faster-executing output — but fewer built-in solutions for app-level needs like code splitting across async routes.

```js
// rollup.config.js — dual CJS + ESM library output
export default {
  input: 'src/index.ts',
  external: ['react', 'react-dom'],   // don't bundle peer deps
  plugins: [typescript(), terser()],
  output: [
    { file: 'dist/index.cjs.js', format: 'cjs', exports: 'named' },
    { file: 'dist/index.esm.js', format: 'es' },
  ],
};
```

The `external` field is critical for libraries — bundling React would ship duplicate React instances in the consumer's app.

> 💡 Senior insight: Vite's production build *is* Rollup. When you tune `rollupOptions` in `vite.config.ts` you are writing a Rollup config.

---

## esbuild

### Q: What does esbuild do, and what does it deliberately not do?

**Trade-off:** esbuild is 10–100× faster than JavaScript-based tools because it's written in Go with parallelism throughout. It handles bundling, transpilation, and minification. It does **not** do TypeScript type-checking, does not run Babel plugins, and its code-splitting is less mature than Rollup's. Use it for speed-critical transform pipelines, not as a standalone app bundler when you need advanced features.

Used by Vite for: dev-time JSX/TS transforms, dependency pre-bundling, and (optionally) production minification.

```ts
// Using esbuild directly (e.g., for a build script)
import * as esbuild from 'esbuild';

await esbuild.build({
  entryPoints: ['src/index.ts'],
  bundle: true,
  minify: true,
  target: ['chrome90', 'firefox88'],
  outfile: 'dist/bundle.js',
});
```

⚠️ Gotcha: `tsc` still needs to run separately for type safety. esbuild strips types — it does not validate them. Wire both into CI.

---

## SWC

### Q: Why did Next.js replace Babel with SWC?

**Trade-off:** SWC (Speedy Web Compiler) is a Rust-based drop-in replacement for Babel transforms and Terser minification. Next.js 12+ uses it by default, achieving 17× faster transforms and 7× faster minification than the Babel equivalent. The trade-off: SWC cannot run arbitrary Babel plugins, so teams with custom Babel transforms need to maintain them or find SWC equivalents.

```json
// next.config.js — SWC is the default; opt back to Babel only if needed
{
  "experimental": {
    "swcPlugins": [["@swc/plugin-emotion", {}]]
  }
}
```

> 💡 Senior insight: If a Next.js app has a `.babelrc` or `babel.config.js`, Next.js **disables SWC and falls back to Babel**. Removing a stale Babel config can be an instant build speed win.

---

## Babel

### Q: Where does Babel still win despite SWC being faster?

**Trade-off:** Babel's AST plugin ecosystem is unmatched. Babel macros, styled-components SSR transforms, babel-plugin-transform-imports for tree-shaking, and custom codemods all rely on Babel's plugin API. For pure transpilation speed Babel loses; for extensibility and legacy pipeline compatibility it remains relevant.

**Transpilation vs polyfilling — the key distinction:**

```json
// babel.config.json
{
  "presets": [
    ["@babel/preset-env", {
      "targets": "> 0.5%, last 2 versions, not dead",
      "useBuiltIns": "usage",   // adds polyfill imports where used
      "corejs": 3
    }],
    "@babel/preset-typescript",
    ["@babel/preset-react", { "runtime": "automatic" }]
  ]
}
```

- `preset-env` **transpiles syntax** (arrow functions, optional chaining) based on `targets`.
- `useBuiltIns: 'usage'` **polyfills APIs** (Promise, Array.from) by injecting core-js imports where those APIs are used.
- `browserslist` in `package.json` or `.browserslistrc` drives `targets` and is shared with tools like PostCSS Autoprefixer.

⚠️ Gotcha: `useBuiltIns: 'usage'` without `corejs` pinned will silently use core-js v2. Always set `"corejs": 3`.

---

## Tree Shaking

### Q: How does tree shaking work, and what breaks it?

**Trade-off:** Tree shaking eliminates unused exports. It works reliably on **statically analyzable ESM** (`import`/`export` must be at the top level, not inside conditions). Anything that confounds static analysis defeats it.

**What enables it:**
- ESM (static `import`/`export`)
- `"sideEffects": false` in `package.json` tells bundlers the package has no side effects on import, allowing unused re-exports to be dropped

```json
// package.json of a utility library
{
  "sideEffects": ["*.css", "*.scss"]  // only CSS files have side effects
}
```

**What breaks it:**

```ts
// ❌ CommonJS — cannot statically analyze
const { debounce } = require('lodash');

// ❌ Dynamic import key — unknowable at build time
import utils from `./utils/${name}`;

// ❌ Barrel file that re-exports everything (see 17-monorepo-nx.md §Barrel Files)
export * from './ComponentA';
export * from './ComponentB';  // bundler must include all unless sideEffects: false

// ✅ Named ESM import — shakeable
import { debounce } from 'lodash-es';
```

> 💡 Senior insight: `lodash` (CJS) vs `lodash-es` (ESM) is the canonical tree-shaking example. Switching is one of the easiest wins auditing a large app. See [07-performance.md] for bundle analysis workflows.

**Follow-ups they'll ask:**
- What is `"sideEffects": false` and who sets it? (Library authors set it on their package; it's a signal to consumer bundlers. Setting it incorrectly will drop CSS imports.)
- How do you verify a barrel file is hurting tree shaking? (`webpack-bundle-analyzer`, `rollup-plugin-visualizer`, or `vite-bundle-visualizer`.)

---

## Code Splitting & Lazy Loading

### Q: Walk me through your code splitting strategy for a large React app.

**Trade-off:** Splitting too aggressively creates waterfall loading; splitting too little bloats the initial bundle. Route-level splitting is almost always worth it; component-level splitting needs profiling to justify the additional request overhead.

```tsx
// Route-level splitting (React Router v6)
import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings  = lazy(() => import('./pages/Settings'));

function App() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings"  element={<Settings />} />
      </Routes>
    </Suspense>
  );
}
```

**Webpack magic comments:**

```ts
const Chart = lazy(() =>
  import(
    /* webpackChunkName: "chart" */
    /* webpackPrefetch: true */      // <link rel="prefetch"> on idle
    './HeavyChart'
  )
);
```

**Vendor chunk strategy (Vite/Rollup):**

```ts
// vite.config.ts
manualChunks(id) {
  if (id.includes('node_modules')) {
    if (id.includes('react')) return 'react-vendor';
    if (id.includes('@tanstack')) return 'query-vendor';
    return 'vendor';
  }
}
```

> 💡 Senior insight: Vendor chunks improve **cache hit rates** for returning users — `react-dom` doesn't change between your deploys but your app code does. Separate them. See [07-performance.md] for LCP/TTI impact analysis.

---

## Source Maps

### Q: What are the source map types and how do you choose?

**Trade-off:** Full source maps enable perfect debugging and error monitoring but expose your original source to anyone who opens DevTools. Balancing debuggability with security is the real decision.

| Type | Build speed | Quality | Use case |
|---|---|---|---|
| `eval` | Fastest | Column-imprecise | Local dev only |
| `cheap-module-source-map` | Fast | Line-precise, no columns | CI / staging |
| `source-map` | Slow | Full fidelity | Prod (hidden upload) |
| `hidden-source-map` | Slow | Full fidelity | Prod + Sentry upload |
| `nosources-source-map` | Medium | Stack trace only | Prod (safe public) |

```ts
// vite.config.ts — production
build: {
  sourcemap: 'hidden',  // generates .map files but omits //# sourceMappingURL comment
}
```

**Error monitoring workflow:** Generate `hidden-source-map`, upload `.map` files to Sentry/Datadog using their CI CLI, then **delete map files from the CDN deployment artifact**. Stack traces are symbolicated server-side; users never see source.

⚠️ Gotcha: `source-map` in production without restricting CDN access means anyone can reconstruct your TypeScript source in under a minute. See [10-security.md] for the full exposure model.

**Follow-ups they'll ask:**
- How do you upload source maps to Sentry in CI? (`@sentry/webpack-plugin` or `@sentry/vite-plugin` with `release` matching your deploy tag.)

---

## Module Formats

### Q: Explain ESM vs CJS and the dual-package pattern.

**Trade-off:** ESM is the future — native browser support, static analysis for tree shaking, top-level await. CJS is Node.js legacy and still required for tooling and older consumers. Libraries need to ship both, which is non-trivial.

```json
// package.json — dual CJS + ESM
{
  "main": "./dist/index.cjs.js",     // CJS consumers (require())
  "module": "./dist/index.esm.js",   // bundler ESM hint (non-standard but widely respected)
  "exports": {
    ".": {
      "import": "./dist/index.esm.js",
      "require": "./dist/index.cjs.js",
      "types": "./dist/index.d.ts"
    }
  },
  "type": "module"                   // treat .js files in this package as ESM
}
```

**Interop pain points:**
- `require()` of ESM is a hard error in older Node versions (< 22 without flag). Pure-ESM libraries (e.g., `chalk` v5, `node-fetch` v3) broke many CJS tools.
- Default exports differ: `module.exports = fn` vs `export default fn` — the CJS `default` key wrapping causes `fn.default` surprise bugs.
- `__dirname`/`__filename` don't exist in ESM; use `import.meta.url` + `fileURLToPath`.

> 💡 Senior insight: `"type": "module"` in `package.json` makes `.js` files ESM. If you need a CJS entrypoint alongside it, name it `.cjs`. This is why modern packages have both `.js` and `.cjs` files.

---

## Next-Generation Tooling

### Q: What is Turbopack and why is everything rewriting in Rust?

**Trade-off:** JavaScript-based build tools are bounded by the V8 single-thread performance ceiling and GC pauses. Rust/Go tools avoid GC entirely, parallelize across all CPU cores natively, and share data through memory rather than serialization. The trade-off is ecosystem maturity — Rust tools lack the plugin breadth of Webpack.

**Current landscape (2026):**

| Tool | Language | Role | Status |
|---|---|---|---|
| **Turbopack** | Rust | Webpack successor (Next.js) | Stable in Next.js 14+ dev, prod beta |
| **Rspack** | Rust | Webpack-API-compatible drop-in | Production-ready |
| **Rolldown** | Rust | Rollup successor (future Vite prod) | Beta |
| **Oxc** | Rust | Parser + linter + transformer | Active |
| **esbuild** | Go | Transform + pre-bundle | Production stable |
| **SWC** | Rust | Babel/Terser replacement | Production stable |

**Rspack** is the pragmatic migration path for teams with large Webpack configs — same API, dramatically faster cold builds. **Turbopack** uses incremental computation (similar to Turborepo's task graph) so only changed files and their transitive dependents recompile.

> 💡 Senior insight: Vite will replace Rollup with Rolldown as the production bundler. The Vite config API stays the same — this is a drop-in performance upgrade, not a migration. Watch the Vite 6/7 roadmap.

---

## Monorepo Build Orchestration

### Q: How does Turborepo/Nx speed up builds across packages?

**Trade-off:** Monorepo tools add a coordination layer above bundlers. They don't replace Vite/Webpack — they decide *which* packages need to rebuild based on file change analysis and cache results of previous runs.

```json
// turbo.json
{
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],       // wait for upstream packages first
      "outputs": ["dist/**", ".next/**"],
      "cache": true
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": []
    }
  }
}
```

Remote caching (Vercel's Turborepo cloud or Nx Cloud) means CI machines share build artifacts — a package that hasn't changed since the last run restores from cache in milliseconds regardless of which machine runs it.

See [17-monorepo-nx.md] for task pipeline details, affected commands, and project graph analysis.

---

## Env Vars at Build Time

### Q: How are environment variables injected into a frontend build, and what are the security implications?

**Trade-off:** Build-time env var replacement (via `define`/`process.env` substitution) bakes values into the bundle at compile time — fast and simple, but the values are visible in the deployed artifact. Runtime config (fetched from an API) is more flexible but adds a request.

**Vite:**
```bash
# .env.production
VITE_API_URL=https://api.example.com
VITE_FEATURE_FLAG=true
# Variables without VITE_ prefix are NOT exposed to the browser
DB_PASSWORD=secret   # stays server-side
```

**Next.js:**
```bash
NEXT_PUBLIC_API_URL=https://api.example.com  # exposed to browser
API_SECRET=hidden                             # server-only (no NEXT_PUBLIC_)
```

**Webpack `DefinePlugin`:**
```js
new webpack.DefinePlugin({
  'process.env.NODE_ENV': JSON.stringify('production'),
  __FEATURE_X__: JSON.stringify(true),
})
```

DefinePlugin performs **string replacement at compile time** — not runtime object injection. `process.env.NODE_ENV === 'production'` in source becomes the literal string `"production" === "production"` which minifiers then constant-fold to `true`, enabling dead-code elimination of dev branches.

⚠️ Gotcha: Any `NEXT_PUBLIC_` or `VITE_` prefixed variable **is shipped in your JS bundle**. API keys, internal service URLs, and feature flags are all readable by anyone who downloads your app. See [10-security.md].

---

## Senior Diagnostic: Slow Build / Huge Bundle

### Q: Walk me through investigating a slow build and an oversized bundle.

This is a systems-thinking question. Structure your answer as hypotheses + tools.

**Slow build — investigation order:**

```
1. Measure: time the full build, then enable verbose/profile mode
   → webpack --profile --json > stats.json  (analyze with webpack.jakoblind.no)
   → vite build --debug

2. Identify hot paths:
   → speed-measure-webpack-plugin (time per loader/plugin)
   → Is ts-loader running tsc? Switch to babel-loader + separate tsc --noEmit in CI

3. Check for missed optimizations:
   → exclude: /node_modules/ on all transform loaders?
   → Webpack persistent cache enabled? (cache: { type: 'filesystem' })
   → Using esbuild-loader or swc-loader instead of babel-loader?

4. Monorepo? → Turborepo/Nx cache hit rate; are outputs declared correctly?

5. CI-specific? → Cache node_modules and .vite / .webpack cache dirs between runs
```

**Huge bundle — investigation order:**

```
1. Visualize:
   → npx vite-bundle-visualizer  (Rollup-based)
   → webpack-bundle-analyzer
   → npx source-map-explorer dist/*.js

2. Common culprits:
   → lodash (CJS, not tree-shakeable) → switch to lodash-es
   → moment.js with all locales → switch to date-fns or day.js
   → Missing dynamic import() on route components
   → Icon library importing everything (e.g., @mui/icons-material)
   → Duplicate packages (two versions of react-query in lockfile)

3. Check tree shaking:
   → Are library package.json files missing "sideEffects"?
   → Barrel files re-exporting everything? (see 17-monorepo-nx.md)
   → Any CommonJS interop preventing shake?

4. Validate vendor chunk strategy:
   → Is react-dom in the vendor chunk (cache-stable)?
   → Are large async components actually splitting?
```

> 💡 Senior insight: Always measure before optimizing. A bundle visualizer takes 30 seconds to run and immediately tells you which package is responsible for 40% of your output. Guessing without it is wasted time.

---

## ⚡ Rapid-Fire

**Q: What's the difference between a loader and a plugin in Webpack?**
Loaders transform individual file types; plugins operate on the full compilation via Webpack's tapable hooks.

**Q: Why is `"type": "module"` in package.json significant?**
It makes all `.js` files in that package ESM. CJS files must then be named `.cjs`.

**Q: What does `webpackPrefetch` do vs `webpackPreload`?**
Prefetch fetches the chunk during browser idle for *future* navigation; preload fetches it in parallel with the current chunk (use for things needed on current page).

**Q: esbuild is faster than Babel — why don't we use it everywhere?**
esbuild has no plugin API equivalent to Babel's, no type checking, and less mature code splitting. It's used where speed matters most (transforms, pre-bundling).

**Q: What is scope hoisting?**
Rollup/Webpack merge small module bodies into a single scope instead of wrapping each in a function, reducing closure overhead and enabling better minification.

**Q: What does `sideEffects: false` in package.json mean?**
Tells bundlers that importing unused exports from this package has no global side effects, enabling full tree shaking of unused modules.

**Q: How does Vite differ in dev vs prod?**
Dev: no bundling, native ESM served on demand, esbuild transforms. Prod: Rollup bundle with full optimization.

**Q: What is Rspack?**
A Rust-based Webpack replacement with API compatibility — same config, dramatically faster builds.

**Q: How do you prevent source maps from leaking proprietary code?**
Use `hidden-source-map`, upload to error monitoring service via CI, exclude `.map` files from CDN deployment.

**Q: What breaks tree shaking most often in a real codebase?**
Barrel files doing `export * from` across large component libraries, combined with packages missing `"sideEffects": false`.

---

## 🚩 Red Flags

- Saying "just use Create React App" for a new production app in 2026 — CRA is unmaintained and webpack-4-based.
- Claiming Vite "doesn't bundle" — it doesn't bundle in dev; it absolutely bundles (via Rollup) for production.
- Treating transpilation and polyfilling as the same thing — they are distinct operations targeting different problems (syntax vs. missing APIs).
- Not knowing what `sideEffects` in package.json does — this is a core library authoring concept.
- Recommending shipping full inline source maps in production without mentioning the security implication.
- Assuming esbuild handles TypeScript type checking — it strips types only, never validates them.
- Over-splitting with lazy imports everywhere without considering waterfall costs or profiling first.
- Not mentioning persistent cache as the first Webpack performance fix — it's the lowest-effort highest-impact option.
- Conflating `NEXT_PUBLIC_` exposure with server-side secrecy — any prefixed variable is in the client bundle.
- Dismissing Webpack entirely — it still owns Module Federation, the primary pattern for runtime microfrontend composition.
