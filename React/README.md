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
| 12 | [`12-system-design.md`](./12-system-design.md) | Frontend system design, micro-frontends, design systems, patterns | The core of senior+ interviews |
| 13 | [`13-senior-interview.md`](./13-senior-interview.md) | Behavioral, leadership, scenario, debugging stories, rapid-fire | Tech alone won't get the senior offer |

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
- **Days 3–5**: React internals — fundamentals, hooks, rendering (03, 04, 05).
- **Days 6–7**: State + performance (06, 07) — practice "why did this re-render" out loud.
- **Days 8–9**: Next.js + RSC mental model (08) — know the App Router caching story cold.
- **Day 10**: Testing (09).
- **Day 11**: Security + a11y (10, 11).
- **Days 12–13**: System design (12) — do 3 mock designs end-to-end.
- **Day 14**: Behavioral (13) — write out 6 STAR stories.

---

*Built as a study kit. Verify framework specifics against the official docs for the version you're targeting (React 19, Next 15 referenced throughout).*
