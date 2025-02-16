# Core React Concepts

1. JSX in React (Add under “Public/Manifest.json”)
  - What is JSX?
  - Why use JSX instead of plain JavaScript?
  - Difference between JSX and HTML.
  - How JSX is compiled using Babel?

2. React Fragments (<React.Fragment>) (Add under “Life Cycle Methods”)
  - Why use Fragments instead of wrapping in <div>?
  - Example usage of <>...</> (shorthand syntax for React.Fragment).

3. Controlled vs Uncontrolled Components (Add under “State Management”)
  - How form inputs are controlled in React.
  - Example of both controlled and uncontrolled inputs.

4. Synthetic Events in React (Add under “Life Cycle Methods”)
  - What are synthetic events?
  - Difference between React synthetic events and native DOM events.
  - Event pooling in React.

# Hooks (Expanding Hooks Section)

1. useImperativeHandle Hook (Add under “Hooks”)
  - How useImperativeHandle is used with forwardRef.
  - Use case for exposing specific DOM methods to parent components.

2. useTransition and useDeferredValue (React 18 features) (Add under “Hooks”)
  - How useTransition allows UI responsiveness when handling state updates.
  - Difference between useDeferredValue and useMemo.

3. useId Hook (React 18 feature)
  - How useId generates unique IDs for accessibility and forms.

# React Advanced Topics

1. React Portal (Add under “Life Cycle Method of Components”)
  - What is a React Portal?
  - When should we use it?
  - Example: Rendering a modal outside the root element.

2. Error Boundaries (Add under “Error Handling”)
  - How to handle runtime errors using componentDidCatch.
  - Example of a simple error boundary component.

3. Re-rendering & Memoization in React (Add under “Performance”)
  - How React decides when to re-render a component.
  - When to use React.memo, useMemo, and useCallback.

# State Management (Expanding Redux/Zustand Section)

1. Comparison Between Redux, Context API, and Zustand
  - When to choose Redux over Context API?
  - Benefits of Zustand vs Redux Toolkit.

2. Redux Middleware (Thunk vs Saga)
  - What is middleware in Redux?
  - How Redux-Thunk and Redux-Saga differ?

# Performance Optimization (Expanding Performance Section)

1. React Concurrent Mode
  - What is Concurrent Mode in React 18?
  - How does it improve UI responsiveness?

2. Shimmer UI Loading & Suspense for Data Fetching
  - How to use Suspense for better user experience.

3. Optimizing Asset Loading (Lazy Loading Images, Code Splitting CSS & JS)
  - How to use Webpack’s splitChunks for optimization.
  - Techniques like lazy-loading images with loading="lazy".

# Security & Best Practices

1. Preventing XSS (Cross-Site Scripting) in React (Add under “Accessibility, Security, Performance, Testability”)
  - Why is dangerouslySetInnerHTML dangerous?
  - How to sanitize user inputs?

2. Avoiding Memory Leaks in React
  - How event listeners cause memory leaks.
  - Why we need cleanup functions inside useEffect.

3. Security Best Practices in React Applications
  - Using HTTPS, avoiding inline styles/scripts.
  - Implementing CSP (Content Security Policy).

# React Ecosystem & Additional Tools

1. Server-Side Rendering (Next.js vs Traditional SSR) (Add under “SSR vs CSR”)
  - How Next.js improves SEO and page load times.
  - Difference between static site generation (SSG) and SSR.

2. React Native vs React for Web
  - Key differences and when to use React Native.

3. Component Testing with React Testing Library vs Jest
  - Difference between Jest and React Testing Library.
  - Example test case for a React component.

# New Questions That Could Be Asked in Interviews

In addition to missing topics, here are some new interview questions you can include:
1. What is the difference between function components and class components?
2. How does React handle reconciliation?
3. What are controlled and uncontrolled inputs in React?
4. What are synthetic events in React, and why do we use them?
5. What is React Fiber, and how does it improve React performance?
6. How do you handle authentication in React using JWT?
7. What are the benefits of React over traditional JavaScript frameworks like jQuery?
8. What are the disadvantages of using React?
9. How do you optimize re-renders in React components?
10. What are some best practices for structuring a React project?
11. How does React handle accessibility (a11y)?
12. How do you manage large-scale applications in React?
13. What is the significance of the key prop in React lists?
14. How does React.lazy() work for code splitting?
15. Why do we need the defaultProps and propTypes in React?