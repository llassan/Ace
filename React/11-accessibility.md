# Accessibility (A11y) in React

Accessibility is the senior differentiator in frontend interviews because it requires you to understand the browser's internal model, platform conventions, and the human cost of getting it wrong. This file covers WCAG, the accessibility tree, keyboard patterns, focus management, ARIA, and how to audit and test components end-to-end.

---

## Why Accessibility Matters

### Q: Why should a business care about accessibility beyond ethics?

**Legal liability is concrete and growing.** The ADA (Americans with Disabilities Act) has been applied to websites since *Robles v. Domino's Pizza* (2019). Section 508 mandates compliance for any entity receiving federal funding. The European Accessibility Act (EAA) took effect in 2025, requiring B2C digital products sold in the EU to meet EN 301 549 (which maps to WCAG 2.1 AA). Lawsuits in the US exceeded 4,000/year by 2023.

**Business case beyond compliance:**
- ~1.3 billion people globally have a disability; that is a direct market segment.
- Accessible sites perform better in SEO — semantic HTML, proper heading hierarchy, alt text, and fast load times are shared signals.
- Accessibility improvements often fix UX for everyone: captions help users in noisy environments, keyboard nav helps power users, high-contrast modes help users in bright sunlight.
- Screen-reader-compatible components are also automation-friendly, lowering QA cost.

> 💡 Senior insight: Frame a11y to stakeholders as "correctness, not charity." A button that only works with a mouse is a bug, not a feature gap. The same engineering discipline that produces good a11y produces resilient, testable UIs.

**Follow-ups they'll ask:**
- What conformance level do you target and why? (AA — AAA is often technically infeasible)
- How do you track a11y regressions in CI?
- Have you worked with a legal or compliance team on VPAT documentation?

---

## The Accessibility Tree

### Q: What is the accessibility tree and how does it differ from the DOM?

The browser builds a parallel **accessibility tree** from the DOM. Each node exposes a computed accessible name, role, state, and properties to platform accessibility APIs (MSAA/UIA on Windows, AX API on macOS). Screen readers, voice control software, and switch devices consume this tree — they do not see pixels.

Key points:
- `role` comes from the HTML element's implicit semantics (`<button>` = `button`, `<nav>` = `navigation`) or an explicit `role` attribute.
- The **accessible name** is computed via the [accessible name calculation algorithm](https://www.w3.org/TR/accname-1.1/): `aria-labelledby` > `aria-label` > native label/title/alt.
- Elements with `display: none` or `visibility: hidden` are removed from the tree. `opacity: 0` or off-screen positioning (used for visually-hidden but readable content) keeps them in the tree.
- CSS order does not change DOM/tree order — only DOM order determines reading/tab order.

> 💡 Senior insight: Open Chrome DevTools → Accessibility panel → select any element to see its computed role, name, and description. This is your ground truth when debugging screen reader behavior.

---

## WCAG — POUR Principles and Conformance

### Q: Walk me through WCAG's structure and what conformance levels mean in practice.

WCAG 2.1/2.2 organizes all success criteria under four **POUR** principles:

| Principle | Core idea | Example SC |
|-----------|-----------|-----------|
| **Perceivable** | Content must be renderable in forms users can perceive | 1.1.1 Non-text Content (alt text), 1.4.3 Contrast |
| **Operable** | UI must be operable via multiple input modalities | 2.1.1 Keyboard, 2.4.3 Focus Order, 2.4.7 Focus Visible |
| **Understandable** | Content and operation must be understandable | 3.3.1 Error Identification, 3.3.2 Labels or Instructions |
| **Robust** | Content must be interpreted by assistive technologies | 4.1.2 Name, Role, Value |

**Conformance levels:**
- **A** — minimum; failing these blocks assistive tech entirely.
- **AA** — industry-standard target; required by ADA/EAA enforcement guidance.
- **AAA** — aspirational; some criteria (e.g., sign language, 7:1 contrast) are not achievable for all content.

**WCAG 2.2 additions worth knowing (2023):**
- 2.4.11 Focus Not Obscured (AA) — focused element must not be fully hidden by sticky headers.
- 2.4.12 Focus Not Obscured Enhanced (AAA).
- 2.5.3 Label in Name (A) — visible label text must be contained in the accessible name.
- 3.2.6 Consistent Help (A) — help mechanisms appear in consistent location.

**Developer-controlled success criteria to memorize:**
`1.1.1`, `1.3.1`, `1.3.5`, `1.4.3`, `1.4.4`, `1.4.10`, `1.4.11`, `2.1.1`, `2.1.2`, `2.4.1`, `2.4.3`, `2.4.7`, `3.3.1`, `3.3.2`, `4.1.2`, `4.1.3`

---

## Semantic HTML First

### Q: Why is a `<div onClick>` a bug, not just a style choice?

A plain `<div>` with an `onClick` handler has no implicit role, no keyboard event handling, and no focusability. A screen reader user hears nothing useful; a keyboard user cannot reach it; a voice control user cannot click it by name.

**Inaccessible:**
```tsx
// Bad — 4 things broken at once
const BadButton = ({ onClick, children }: { onClick: () => void; children: React.ReactNode }) => (
  <div onClick={onClick} style={{ cursor: 'pointer' }}>
    {children}
  </div>
);
```

**Accessible:**
```tsx
// Good — use the element whose semantics already match the intent
const GoodButton = ({ onClick, children }: { onClick: () => void; children: React.ReactNode }) => (
  <button type="button" onClick={onClick}>
    {children}
  </button>
);
```

`<button>` gives you for free: `role="button"`, keyboard activation on Enter and Space, `:focus-visible` support, `disabled` state propagation to the accessibility tree, and form association.

**Landmark elements to use:**

```tsx
<header>       {/* role="banner" — one per page */}
<nav>          {/* role="navigation" — label with aria-label if multiple */}
<main>         {/* role="main" — one per page */}
<aside>        {/* role="complementary" */}
<footer>       {/* role="contentinfo" */}
<section>      {/* role="region" — only meaningful with an accessible name */}
<article>      {/* role="article" — self-contained content */}
```

**Heading hierarchy:**
- One `<h1>` per page, representing the page title.
- Do not skip levels (h1 → h3) for visual sizing — use CSS for that.
- Screen reader users navigate by heading level as a table of contents.

> 💡 Senior insight: The first rule of ARIA (from W3C): "No ARIA is better than bad ARIA." Always reach for a native element first. If you must use a div, you are taking on the full burden of role, keyboard, focus, and state management manually.

⚠️ Gotcha: `<button>` inside `<form>` defaults to `type="submit"`. Always specify `type="button"` for non-submit buttons or you will trigger unexpected form submissions.

---

## ARIA

### Q: When should you actually use ARIA, and what are the most common mistakes?

Use ARIA **only** when no native HTML element covers your use case (custom widgets like comboboxes, tabs, tree views) or when you need to augment existing semantics (live regions, expanded state).

**Core ARIA categories:**
- **Roles** — `role="dialog"`, `role="tablist"`, `role="combobox"`, `role="status"`
- **States** — `aria-expanded`, `aria-selected`, `aria-checked`, `aria-disabled`, `aria-invalid`
- **Properties** — `aria-label`, `aria-labelledby`, `aria-describedby`, `aria-controls`, `aria-owns`, `aria-haspopup`

**Labeling patterns:**

```tsx
// aria-label — inline string, no visible text needed
<button aria-label="Close dialog">
  <XIcon aria-hidden="true" />
</button>

// aria-labelledby — references visible text by ID (preferred; localizes automatically)
<h2 id="dialog-title">Confirm Deletion</h2>
<div role="dialog" aria-labelledby="dialog-title" aria-modal="true">
  ...
</div>

// aria-describedby — supplemental description (not the name)
<input
  id="email"
  type="email"
  aria-describedby="email-hint email-error"
/>
<span id="email-hint">We'll never share your email.</span>
<span id="email-error" role="alert">Please enter a valid email address.</span>
```

**aria-live regions for dynamic content:**

```tsx
// polite — announces after current speech finishes (status messages, counts)
<div aria-live="polite" aria-atomic="true">
  {status}
</div>

// assertive — interrupts immediately (errors, critical alerts)
<div aria-live="assertive" role="alert">
  {criticalError}
</div>
```

⚠️ Gotcha: `role="alert"` implies `aria-live="assertive"` and `aria-atomic="true"`. Mounting the element with content already inside it may not trigger an announcement — insert content *after* mount, or use a pattern that removes/re-adds the element.

**Common ARIA mistakes:**

```tsx
// Redundant role — <button> already has role="button"
<button role="button">Submit</button>  // BAD

// Broken reference — aria-labelledby points to nonexistent ID
<div role="dialog" aria-labelledby="missing-id">...</div>  // BAD

// aria-hidden on focusable element — keyboard users reach it, AT ignores it
<button aria-hidden="true">Invisible to AT, reachable by keyboard</button>  // BAD

// Missing aria-hidden on decorative icon inside labeled button
<button aria-label="Delete">
  <TrashIcon />  {/* BAD — AT reads icon title + aria-label */}
</button>

// Correct
<button aria-label="Delete">
  <TrashIcon aria-hidden="true" />
</button>
```

---

## Keyboard Accessibility

### Q: What are the rules for keyboard interaction and how does tabindex work?

Every interactive element must be reachable and operable with a keyboard. WCAG 2.1.1 (Level A) is a hard requirement.

**tabindex values:**
- `tabIndex={0}` — element joins natural tab order (only needed for non-interactive elements you make interactive, like a custom widget container).
- `tabIndex={-1}` — element is focusable programmatically (via `.focus()`) but not in tab order — used for managing focus within composite widgets and modals.
- `tabIndex > 0` — antipattern; creates a separate, confusing tab order. Never use in practice.

**Skip links:**

```tsx
// Place as first element in <body>; visually hidden until focused
const SkipLink = () => (
  <a
    href="#main-content"
    className="skip-link"
    /* CSS: position absolute; transform: translateY(-100%); :focus { transform: none } */
  >
    Skip to main content
  </a>
);

<main id="main-content" tabIndex={-1}>
  {/* tabIndex={-1} allows programmatic focus when skip link is activated */}
</main>
```

**Keyboard patterns per WAI-ARIA Authoring Practices Guide (APG):**

| Widget | Keys |
|--------|------|
| Button | Enter, Space |
| Checkbox | Space to toggle |
| Dialog | Escape to close, Tab/Shift+Tab within trap |
| Tabs | Arrow keys between tabs, Tab into panel |
| Combobox | Arrow keys in list, Enter to select, Escape to close |
| Menu | Arrow keys, Enter/Space to activate, Escape to close |
| Tree | Arrow keys, Enter/Space to select/expand |

⚠️ Gotcha: Keyboard traps are a WCAG failure (2.1.2) EXCEPT in modal dialogs where trapping focus is the correct, expected behavior. The difference is that modals must provide an explicit way to dismiss (Escape key, close button).

---

## Focus Management in SPAs

### Q: How do you handle focus when navigating between routes in a React SPA?

In a traditional multi-page app, every navigation moves focus to the top of the document. SPAs break this — the URL changes but focus stays on the link that was clicked, or worse, gets lost entirely.

**Route-change focus pattern:**

```tsx
import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

const RouteAnnouncer = () => {
  const location = useLocation();
  const headingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    // Move focus to the page heading after route change
    headingRef.current?.focus();
  }, [location.pathname]);

  return (
    <h1 tabIndex={-1} ref={headingRef}>
      {pageTitle}
    </h1>
  );
};
```

**focus-visible vs :focus:**

```css
/* Never suppress :focus entirely */
/* Bad */
*:focus { outline: none; }

/* Good — hide ring for mouse, show for keyboard */
*:focus:not(:focus-visible) { outline: none; }
*:focus-visible { outline: 2px solid #005fcc; outline-offset: 2px; }
```

**Accessible modal with full focus management:**

```tsx
import { useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';

const FOCUSABLE = [
  'a[href]', 'button:not([disabled])', 'input:not([disabled])',
  'select:not([disabled])', 'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(', ');

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

const Modal = ({ isOpen, onClose, title, children }: ModalProps) => {
  const dialogRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<Element | null>(null);

  useEffect(() => {
    if (isOpen) {
      // Save the element that opened the modal
      triggerRef.current = document.activeElement;
      // Move focus into dialog on next tick
      const firstFocusable = dialogRef.current?.querySelector<HTMLElement>(FOCUSABLE);
      firstFocusable?.focus();
    } else {
      // Restore focus to trigger element on close
      (triggerRef.current as HTMLElement)?.focus();
    }
  }, [isOpen]);

  const trapFocus = useCallback((e: KeyboardEvent) => {
    if (e.key !== 'Tab' || !dialogRef.current) return;
    const focusable = [...dialogRef.current.querySelectorAll<HTMLElement>(FOCUSABLE)];
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    document.addEventListener('keydown', trapFocus);
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('keydown', trapFocus);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, trapFocus, onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div
      role="presentation"
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)' }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        style={{ background: 'white', padding: '2rem', borderRadius: '8px' }}
      >
        <h2 id="modal-title">{title}</h2>
        {children}
        <button type="button" onClick={onClose}>
          Close
        </button>
      </div>
    </div>,
    document.body
  );
};
```

> 💡 Senior insight: In production, prefer battle-tested primitives for complex widgets: **Radix UI**, **React Aria** (Adobe), or **Headless UI**. They handle all edge cases including iOS VoiceOver, Windows High Contrast mode, and pointer vs keyboard distinctions. Building your own modal is a great learning exercise; shipping your own modal to 10M users is a risk.

---

## Forms Accessibility

### Q: What does an accessible form look like end to end?

**Inaccessible form:**
```tsx
// BAD — no labels, error not associated, placeholder as label
const BadForm = () => (
  <form>
    <input type="email" placeholder="Email address" />
    <span style={{ color: 'red' }}>Invalid email</span>
    <button>Submit</button>
  </form>
);
```

**Accessible form:**
```tsx
const AccessibleForm = () => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const errorId = 'email-error';

  return (
    <form noValidate onSubmit={handleSubmit}>
      <label htmlFor="email">
        Email address
        <span aria-hidden="true"> *</span>
      </label>
      <input
        id="email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        aria-required="true"
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={error ? errorId : undefined}
        autoComplete="email"
      />
      {error && (
        <span id={errorId} role="alert">
          {error}
        </span>
      )}

      {/* Group related fields */}
      <fieldset>
        <legend>Notification preferences</legend>
        <label>
          <input type="checkbox" name="email-notify" />
          Email notifications
        </label>
        <label>
          <input type="checkbox" name="sms-notify" />
          SMS notifications
        </label>
      </fieldset>

      <button type="submit">Create account</button>
    </form>
  );
};
```

Key rules:
- Every `<input>` needs an associated `<label>` (via `htmlFor`/`id` or wrapping).
- `placeholder` is not a label substitute — it disappears on input and has insufficient contrast.
- `aria-invalid="true"` signals error state to AT.
- `aria-describedby` links the input to its error message; `role="alert"` announces it on insertion.
- `aria-required="true"` or the native `required` attribute.
- Group related controls with `<fieldset>` + `<legend>`.
- `autoComplete` attributes help users with cognitive disabilities and motor impairments.

---

## Color, Contrast, and Motion

### Q: What are the contrast requirements and how do you handle motion sensitivity?

**WCAG contrast ratios (1.4.3 — Level AA):**
- Normal text (< 18pt / < 14pt bold): **4.5:1** minimum
- Large text (≥ 18pt / ≥ 14pt bold): **3:1** minimum
- UI components and graphical objects (1.4.11): **3:1** against adjacent color

**Do not rely on color alone (1.4.1):** Error states need more than a red border — add an icon, text label, or pattern. Colorblind users see ~8% of males.

**prefers-reduced-motion:**

```tsx
// CSS
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

// React hook
const useReducedMotion = () => {
  const [reduced, setReduced] = useState(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches
  );
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);
  return reduced;
};
```

**prefers-color-scheme:** Implementing dark mode as a CSS media query is the accessible baseline. Offering a manual toggle respects user preference without requiring OS-level changes.

---

## Images and Media

### Q: When should alt text be empty vs descriptive?

| Image type | alt value |
|------------|-----------|
| Informative | Concise description of what it conveys |
| Decorative (background, icon next to visible text) | `alt=""` (empty string, not omitted) |
| Functional (icon-only button, logo as link) | Describe the function, not the appearance |
| Complex (chart, graph) | Short alt + long description via `aria-describedby` or adjacent text |
| Text in image | Reproduce the text exactly |

Omitting `alt` entirely causes some screen readers to read the file path — always include the attribute.

**Media requirements:**
- Audio/video needs captions (1.2.2, Level A) and transcripts.
- Auto-playing audio that lasts > 3 seconds is a WCAG failure unless the user can stop it.

---

## Testing Accessibility

### Q: What does a complete a11y testing strategy look like?

Automated tools catch an estimated **30–40%** of WCAG issues. A complete strategy requires multiple layers.

**1. Unit/integration: jest-axe**

```tsx
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

test('Modal has no axe violations', async () => {
  const { container } = render(
    <Modal isOpen title="Confirm">Content</Modal>
  );
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

**2. E2E: Playwright + axe-core**

```ts
import { checkA11y, injectAxe } from 'axe-playwright';

test('home page passes axe', async ({ page }) => {
  await page.goto('/');
  await injectAxe(page);
  await checkA11y(page, undefined, {
    axeOptions: { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] } },
  });
});
```

**3. Manual — keyboard-only pass checklist:**
- Tab through every interactive element in order.
- Every focus state is visible.
- All actions completable without mouse.
- No keyboard traps (except modals, which must close on Escape).
- Skip link is present and works.

**4. Screen reader testing:**
- macOS: VoiceOver (Cmd+F5) + Safari (best AT/browser pairing on Mac).
- Windows: NVDA (free) + Firefox or Chrome.
- iOS: VoiceOver + Safari.
- Android: TalkBack + Chrome.

**5. Lighthouse a11y score** — useful for regression detection in CI, not a compliance metric. Score of 100 does not mean WCAG AA compliant.

> 💡 Senior insight: Automated tests are your safety net, not your proof. A form with all green axe results can still fail if the label text says "Field 1" — axe checks structure, not meaning. Pair automated checks with content review and real user testing.

See also: file 09 (Testing) for RTL and Playwright setup patterns.

---

## Senior Scenario: A11y Audit Walkthrough

### Q: How would you audit an existing component for accessibility issues?

Given a `Dropdown` component, walk through this checklist:

**Structure:**
- [ ] Trigger is a `<button>` with descriptive accessible name.
- [ ] List container has `role="listbox"` or `role="menu"` depending on widget type.
- [ ] Each option has `role="option"` or `role="menuitem"`.
- [ ] `aria-expanded` on trigger reflects open/closed state.
- [ ] `aria-controls` on trigger references list ID.
- [ ] `aria-activedescendant` or roving tabindex for option focus.

**Keyboard:**
- [ ] Enter/Space opens the dropdown.
- [ ] Arrow keys move between options.
- [ ] Escape closes and returns focus to trigger.
- [ ] Home/End jump to first/last option (APG pattern).
- [ ] Printable characters jump to matching option (type-ahead).

**Screen reader:**
- [ ] Announcing "expanded" or "collapsed" on toggle.
- [ ] Selected option announced on selection.
- [ ] Count announced ("1 of 8") if list role supports it.

**Visual:**
- [ ] Contrast ≥ 4.5:1 for option text.
- [ ] Focus ring visible on trigger and active option.
- [ ] Not relying on color alone for selected state.

**Code inspection:**
- [ ] No `aria-hidden` on focusable elements.
- [ ] No `tabindex > 0`.
- [ ] ARIA references (`aria-labelledby`, `aria-describedby`, `aria-controls`) point to real existing IDs.
- [ ] No missing `id` attributes on referenced elements.

> 💡 Senior insight: The WAI-ARIA Authoring Practices Guide (APG) at https://www.w3.org/WAI/ARIA/apg/ has a canonical pattern with full keyboard spec and working examples for every widget type. Reference it directly in code reviews.

---

## ⚡ Rapid-Fire

**What does `aria-modal="true"` do?** Tells AT that content outside the dialog should be treated as inert. Without it, VoiceOver users can navigate outside a modal via the virtual cursor. Note: browser support for actually inert-ing the background is inconsistent — pair with `inert` attribute on background content.

**What is the `inert` attribute?** An HTML attribute that makes an element and all its descendants non-interactive and hidden from AT. Use on background content when a modal is open.

**What is the accessible name for `<img src="logo.png" />`?** The file name ("logo.png") — always provide `alt`.

**When does `role="presentation"` differ from `aria-hidden="true"`?** `role="presentation"` removes element semantics but keeps descendants visible to AT. `aria-hidden="true"` removes the element and all descendants from the tree entirely.

**Can you make `<div>` keyboard focusable?** Yes, with `tabIndex={0}`. But you also need `role`, `onKeyDown` for Enter/Space, and all state management — always prefer a native element.

**What is ARIA 1.2's `aria-description`?** A new property (ARIA 1.2) equivalent to inline `aria-describedby` without requiring a separate element with an ID. AT support is still maturing.

**What is the difference between `role="button"` and `type="submit"`?** None from a role perspective — both expose `role="button"`. The difference is behavior: `type="submit"` triggers form submission; `type="button"` does not.

**What CSS property is used to visually hide content while keeping it in the accessibility tree?** The "visually-hidden" utility: `position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap;`. Do NOT use `display: none` or `visibility: hidden`.

**What is `aria-live="off"`?** The default; region changes are not announced. Useful to explicitly disable live behavior on a container that contains a live region descendant.

**Lighthouse a11y score of 100 means WCAG AA compliant?** No. Automated tools cover ~30-40% of criteria. A score of 100 means axe found no automated violations; it says nothing about color meaning, logical heading structure quality, or meaningful alt text.

---

## 🚩 Red Flags

- Suppressing `:focus` styles globally without providing a `:focus-visible` replacement.
- Using `tabIndex={1}` or higher anywhere in the codebase.
- Using `<div onClick>` for interactive elements without adding `role`, `tabIndex`, and keyboard handlers.
- Adding `aria-label` to a `<div>` with no role — label without role has no effect.
- `aria-hidden="true"` on an element that contains a focusable descendant.
- `aria-labelledby` or `aria-describedby` referencing an ID that does not exist in the DOM.
- Live regions that are mounted with content already inside them (announcement may not fire).
- Modals that do not trap focus or restore focus on close.
- Error messages not programmatically associated with their inputs.
- Placeholder text used as the sole label for an input.
- Building custom dropdowns, date pickers, or tree views from scratch instead of using tested primitives.
- "We'll add accessibility later" — retrofitting is 10x more expensive than building it in.
