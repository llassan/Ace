# Senior React Interview Prep (6–7 YOE)

A deep, opinionated interview-preparation kit for **senior / lead front-end engineers**. This is not a "what is JSX" cheat sheet — it assumes you ship React in production and an interviewer will probe *trade-offs, failure modes, and judgment*, not definitions.

> **How to use this**: Read top-to-bottom for a full refresh, or jump to a weak area. Every file ends with a **Rapid-Fire** section (quick recall) and **Red Flags** (answers that make a senior look junior). Practice saying the answers out loud — interviews reward articulation, not recognition.

---

## 📁 Structure

| # | File | What it covers | Why it matters at senior level |
|---|------|----------------|--------------------------------|
| — | [`README.md`](./README.md) | Index, study plan, interview format | Orientation |
| 01 | [`01-javascript-core.md`](./01-javascript-core.md) | Closures, prototypes, event loop, async, `this`, modules, memory | React is JS; bugs are usually JS bugs |
| 02 | [`02-typescript.md`](./02-typescript.md) | Generics, narrowing, utility types, typing components/hooks, `infer` | Senior React = typed React |
| 03 | [`03-react-fundamentals.md`](./03-react-fundamentals.md) | JSX, components, props/state, events, lifecycle, error boundaries | Foundations you'll be expected to *explain*, not list |
| 04 | [`04-hooks.md`](./04-hooks.md) | All hooks, rules, custom hooks, closures-in-hooks, React 19 hooks | The #1 source of senior-level bugs |
| 05 | [`05-rendering-reconciliation.md`](./05-rendering-reconciliation.md) | Virtual DOM, Fiber, diffing, keys, render phases, batching, concurrent | "Why did this re-render?" is a senior question |
| 06 | [`06-state-management.md`](./06-state-management.md) | Context, Redux Toolkit, Zustand, Jotai, TanStack Query, server vs client state | Choosing the right tool is the real skill |
| 07 | [`07-performance.md`](./07-performance.md) | Memoization, code splitting, profiling, Web Vitals, list virtualization | You'll be asked to *diagnose*, not just optimize |
| 08 | [`08-nextjs.md`](./08-nextjs.md) | SSR/SSG/ISR, App Router, RSC, Server Actions, caching, streaming | The default production stack in 2025+ |
| 09 | [`09-testing.md`](./09-testing.md) | RTL, Jest/Vitest, Playwright, mocking, testing strategy & pyramid | Seniors own quality, not just code |
| 10 | [`10-security.md`](./10-security.md) | XSS, CSRF, auth/token storage, RBAC, dependency & supply-chain risk | Front-end is an attack surface |
| 11 | [`11-accessibility.md`](./11-accessibility.md) | WCAG, ARIA, keyboard nav, focus management, semantic HTML | Often the differentiator in senior loops |
| 12 | [`12-system-design.md`](./12-system-design.md) | Frontend system design, micro-frontends, worked examples (feed/grid/typeahead) | The core of senior+ interviews |
| 13 | [`13-senior-interview.md`](./13-senior-interview.md) | Behavioral, leadership, scenario, debugging stories, rapid-fire | Tech alone won't get the senior offer |
| 14 | [`14-react-patterns.md`](./14-react-patterns.md) | HOC, render props, compound, provider, headless, container/presentational | Know why each faded or survived |
| 15 | [`15-data-fetching.md`](./15-data-fetching.md) | Fetch/Axios, races & cancellation, TanStack Query mechanics, WebSocket/SSE/polling | Most bugs are fetch-correctness bugs |
| 16 | [`16-routing.md`](./16-routing.md) | React Router (data routers), protected routes, RBAC, History API | Routing + access control come up constantly |
| 17 | [`17-frontend-architecture.md`](./17-frontend-architecture.md) | Folder structure, monorepos (Nx/Turborepo), design systems, micro-frontends | Codebase/team architecture vs product design |
| 18 | [`18-browser-internals.md`](./18-browser-internals.md) | Critical Rendering Path, reflow/repaint, layout thrashing, storage, networking | The layer beneath React that explains perf |
| 19 | [`19-build-tools-bundlers.md`](./19-build-tools-bundlers.md) | Webpack/Vite/Rollup/esbuild/SWC/Babel, tree-shaking, source maps | How source becomes an optimized bundle |
| 20 | [`20-cicd.md`](./20-cicd.md) | GitHub Actions, Docker, pipelines, feature flags, release strategies | Seniors own shipping, not just code |
| 21 | [`21-common-interview-questions.md`](./21-common-interview-questions.md) | Consolidated cram bank — crisp answers + deep-dive pointers | The day-before revision sheet |

---

## 🔗 Maps to the full 0–7 YOE topic outline

This kit covers the entire 23-section preparation outline; some sections are merged where they overlap:

| Outline section | Covered in |
|---|---|
| 1. JavaScript Fundamentals | `01` (incl. currying, polyfills, GC) |
| 2. React Fundamentals | `03` |
| 3. React Lifecycle | `03` (class lifecycle ↔ hooks mapping) + `04` |
| 4. React Hooks | `04` |
| 5. Advanced Hooks | `04` (custom hooks, pitfalls) + `14` (hook patterns) |
| 6. State Management | `06` |
| 7. React Patterns | `14` |
| 8. React Performance | `07` |
| 9. React Internals | `05` |
| 10. TypeScript for React | `02` |
| 11. Data Fetching | `15` (+ `06` for server-state philosophy) |
| 12. Routing | `16` |
| 13. Next.js | `08` |
| 14. Frontend Architecture | `17` (+ `12` for product design) |
| 15. Security | `10` |
| 16. Accessibility | `11` |
| 17. Testing | `09` |
| 18. Browser Internals | `18` |
| 19. Build Tools & Bundlers | `19` (+ `07` for bundle perf) |
| 20. CI/CD | `20` |
| 21. Frontend System Design | `12` |
| 22. Leadership & Senior-Level | `13` |
| 23. Common Interview Questions | `21` |

---

## 🎯 The senior interview, decoded

A 6–7 YOE React loop is usually 4–6 rounds:

1. **Live coding / pairing** — build a component, debug a broken one, or implement a hook. They watch *how you think*, not whether you finish.
2. **Front-end system design** — "Design Twitter's feed", "Design a data table for 1M rows", "Design a design system". → file 12.
3. **Deep technical / architecture** — rendering, state, performance, trade-offs. → files 03–07.
4. **Behavioral / leadership** — mentoring, conflict, ownership, incidents. → file 13.
5. **(Sometimes) Domain rounds** — testing, a11y, security, or a take-home review.

**What separates senior from mid-level answers:**

| Mid-level says… | Senior says… |
|---|---|
| "Use `useMemo` to make it faster." | "Profile first — `useMemo` only helps if the computation is expensive *and* deps are stable; otherwise it adds overhead." |
| "Redux for state." | "Server state → TanStack Query; UI state → local/Zustand. Reaching for Redux for cache is the usual mistake." |
| "It re-renders because state changed." | "It re-renders because the parent re-rendered and the prop is a new object identity each render." |
| "I'd add tests." | "I'd test behavior at the integration boundary, mock the network not the modules, and keep the pyramid honest." |

Lead with the **trade-off and the failure mode**. That's the tell.

---

## 🗓️ Suggested 2-week plan

- **Days 1–2**: JS core + TypeScript (01, 02) — the foundation everything else leans on.
- **Days 3–5**: React internals — fundamentals, hooks, rendering, patterns (03, 04, 05, 14).
- **Days 6–7**: State + data fetching + performance (06, 15, 07) — practice "why did this re-render" out loud.
- **Day 8**: Routing + browser internals (16, 18) — CRP and reflow/repaint cold.
- **Day 9**: Next.js + RSC mental model (08) — know the App Router caching story cold.
- **Day 10**: Testing + build tools + CI/CD (09, 19, 20).
- **Day 11**: Security + a11y (10, 11).
- **Days 12–13**: Architecture + system design (17, 12) — do 3 mock designs end-to-end.
- **Day 14**: Behavioral (13) + skim the cram sheet (21) — write out 6 STAR stories.

> **Crunched for time?** Read [`21-common-interview-questions.md`](./21-common-interview-questions.md) first — it's the consolidated cram sheet with pointers into every deep-dive.

---

*Built as a study kit. Verify framework specifics against the official docs for the version you're targeting (React 19, Next 15 referenced throughout).*
