# React Lifecycle, Hooks, and Key Concepts

## Why do we need a Framework?

Frameworks provide a structured and efficient way to build modern web applications. 
By using frameworks, developers can focus more on solving business problems rather than reinventing the wheel for common functionalities.

## Why React.js?

React.js is a flexible and efficient JavaScript library for building user interfaces. 
It uses a component-based architecture, enabling reusable and maintainable code, and a Virtual DOM for optimized rendering and better performance. 
Its declarative syntax simplifies UI development, while its large ecosystem and community provide extensive tools and resources. 
React is versatile, working seamlessly with libraries for state management (e.g., Redux) and routing, and it supports cross-platform development through tools like React Native. 
Backed by Facebook and widely used by major companies, React is a reliable choice for scalable, dynamic applications.

## What is JSX?
JSX is a XML-like syntax extension to ECMAScript (the acronym stands for JavaScript XML). Basically it just provides syntactic sugar for the React.createElement() function, giving us expressiveness of JavaScript along with HTML like template syntax.

In the example below text inside <h1> tag is returned as JavaScript function to the render function.
```jsx harmony
class App extends React.Component {
  render() {
    return(
      <div>
        <h1>{'Welcome to React world!'}</h1>
      </div>
    )
  }
}
```

## What are the lifecycle methods of React?

React lifecycle methods are special functions that allow you to hook into different stages of a component’s life (mounting, updating, and unmounting). 


React Lifecycle Methods are categorized based on the component’s lifecycle stages:

1. **Mounting**: Mounting refers to adding the elements into the browser DOM. This phase includes lifecycle methods like:
	- constructor(): Used for initializing state and binding event handlers.
	- static getDerivedStateFromProps(props, state): Updates state based on props before rendering (rarely used).
	- render(): Required method that returns the JSX to render the component.
	- componentDidMount(): Executes after the component is rendered in the DOM. Ideal for API calls, subscriptions, or setting up listeners.

2. **Updating (When the component’s props or state changes)**:
	- static getDerivedStateFromProps(props, state): Also called during updates to sync state with new props.
	- shouldComponentUpdate(nextProps, nextState): Determines whether the component should re-render (used for optimization).
	- render(): Re-renders the UI based on updated props or state.
	- getSnapshotBeforeUpdate(prevProps, prevState): Captures some information (e.g., scroll position) before the DOM updates.
	- componentDidUpdate(prevProps, prevState, snapshot): Called after the DOM is updated. Useful for DOM manipulations or making API calls after state updates.

3. **Unmounting (When the component is removed from the DOM)**:
	•	componentWillUnmount():
Used for cleanup tasks like removing event listeners, canceling subscriptions, or clearing timers.

4. **Error Handling (When an error occurs in the component)**:
	•	static getDerivedStateFromError(error):
Updates state to display a fallback UI during an error.
	•	componentDidCatch(error, info):
Logs errors and additional info, useful for error reporting.

Key Points for Functional Components:

With React Hooks, functional components can now handle lifecycle methods using:
	•	useEffect(): Handles componentDidMount, componentDidUpdate, and componentWillUnmount in a unified way.
	•	useState() and useContext(): Replace constructor and state management.

This structured breakdown is concise and perfect for an interview context.

## What are the different phases of the component lifecycle?

There are four different phases in the lifecycle of a React component:

1. **Initialization**: 
   - During this phase, React component will prepare by setting up the default props and initial state for the upcoming journey.

2. **Mounting**: 
   - Mounting refers to adding the elements into the browser DOM. React uses the Virtual DOM, meaning the entire browser DOM is not refreshed. This phase includes lifecycle methods like `componentWillMount` and `componentDidMount`.

3. **Updating**: 
   - A component will be updated when there is a change in its state or props. Lifecycle methods involved in this phase include `componentWillUpdate`, `shouldComponentUpdate`, `render`, and `componentDidUpdate`.

4. **Unmounting**: 
   - In the last phase, the component will be removed from the DOM. The lifecycle method `componentWillUnmount` is invoked during this phase.

## Types of Hooks in React

### 1. Built-in Hooks

- **Basic Hooks**:
  - `useState()`: Sets and retrieves the state in a functional component.
  - `useEffect()`: Enables side-effects in functional components (e.g., data fetching).
  - `useContext()`: Creates a shared state accessible to multiple components without passing props down manually.

- **Additional Hooks**:
  - `useReducer()`: Used for complex state logic or when the next state depends on the previous one. Helps optimize performance by triggering fewer re-renders.
  - `useMemo()`: Memoizes a value to avoid expensive recalculations on each render.
  - `useCallback()`: Optimizes callback functions passed to child components to avoid unnecessary re-renders.
  - `useImperativeHandle()`: Modifies the instance that will be passed with the `ref` object.
  - `useDebugValue()`: Displays custom hook information in React DevTools.
  - `useRef()`: Creates a reference to a DOM element in functional components.
  - `useLayoutEffect()`: Reads the layout from the DOM and re-renders synchronously.

## Do Hooks cover all the functionalities provided by the classes?

While React Hooks aim to cover all functionalities of class components, some methods are not yet available with Hooks:

- `getSnapshotBeforeUpdate()`
- `getDerivedStateFromError()`
- `componentDidCatch()`

As of now, third-party libraries might not be fully compatible with Hooks, but this is expected to change in the future.

## What is React Router?

React Router is the standard library used for routing in React. It allows the creation of single-page applications (SPA) by navigating between different views without refreshing the entire page. React Router synchronizes the browser URL with the UI.

### Major Components of React Router:

- **BrowserRouter**: 
  - Uses the HTML5 history API (`pushState`, `popstate`, and `replaceState`) to synchronize the UI with the URL.

- **Routes**: 
  - A newer component in React v6 for rendering route-based UI.

- **Route**: 
  - A conditional component that renders UI when the current URL matches the specified `path`.

- **Link**: 
  - Creates links to different routes, similar to anchor tags in HTML.

## Can web browsers read JSX directly?

No, web browsers cannot read JSX directly because JSX is not a regular JavaScript object. To enable the browser to read JSX, it must first be transformed into plain JavaScript using a tool like **Babel**.

## Why use React instead of other frameworks like Angular?

- **Easy creation of dynamic applications**: React reduces the complexity of code and allows easier creation of dynamic applications.
- **Improved performance**: React uses the Virtual DOM to update only the changed components, improving performance.
- **Reusable components**: React components are reusable, making it easier to manage complex applications.
- **Unidirectional data flow**: React uses a single data flow, making it easier to debug.
- **Dedicated debugging tools**: React provides tools like the React Developer Tools Chrome extension to simplify debugging.

## What is an event in React?

An event in React is an action triggered by the user or system, such as pressing a key or clicking a mouse. 

- React events use camelCase naming conventions instead of lowercase (as used in HTML).
- Event handlers are passed as functions in JSX, rather than as strings in HTML.

## What are synthetic events in React?

- Synthetic events are a cross-browser wrapper for native browser events that ensure consistent behavior across all browsers.
- Methods like `preventDefault()` are part of the synthetic event system.

## What are error boundaries?

Error boundaries are React components that catch JavaScript errors anywhere in their child component tree, log those errors, and display a fallback UI instead of crashing the component tree.

### Where can error boundaries detect errors?

- **Render phase**
- **Inside lifecycle methods**
- **Inside the constructor**

## Common React Interview Questions

1. **When would you use refs in React?**
   - Refs are used to directly access a DOM element, especially when interacting with child components or altering an element's value.

2. **When would you use `useMemo()` in React?**
   - `useMemo()` is used to cache values and avoid expensive calculations on each render, improving performance.

3. **Why would you use super constructors with props arguments?**
   - Super constructors are used to pass props to the parent class constructor, enabling access to `this.props` within the component.

4. **How would you avoid binding in React?**
   - Use arrow functions in class properties to avoid binding, eliminating the need to bind methods in the constructor.

5. **Which method would you use to handle events in React?**
   - In React, events are handled using camelCase naming conventions. Functions are passed as event handlers in JSX instead of strings.

## Strict Mode in React

Strict Mode in React is a development tool that helps identify potential problems in your application. It currently addresses the following issues:

- **Identifying components with unsafe lifecycle methods**:  
  StrictMode helps detect the usage of deprecated lifecycle methods that are unsafe in asynchronous React applications. It provides warnings if any class components use unsafe lifecycle methods.
  
- **Warning about the usage of legacy string refs**:  
  If you are using string refs (an older method for managing refs in React), StrictMode will give you a warning to encourage the use of the recommended callback refs.
  
- **Warning about the usage of `findDOMNode()`**:  
  The `findDOMNode()` method has been deprecated in React. StrictMode provides warnings when this method is used, encouraging developers to avoid it.
  
- **Warning about the usage of legacy context API**:  
  React's legacy context API is error-prone, and StrictMode warns when it is used, urging developers to migrate to the new context API.

## Different Ways to Style a React Component

React offers several ways to style components, allowing flexibility and scalability in design. Here are a few approaches:

1. **Inline Styling**:  
   You can apply styles directly using the `style` attribute in JSX. The value of `style` must be a JavaScript object with camelCased properties.
   ```jsx
   const divStyle = { color: 'blue', backgroundColor: 'yellow' };
   return <div style={divStyle}>Hello, World!</div>;
   ```




2. **Using JavaScript Object**:
You can create a JavaScript object with your style properties and use it as the value for the style attribute.

```jsx
const buttonStyle = { fontSize: '20px', padding: '10px' };
return <button style={buttonStyle}>Click Me</button>;
```
3. **CSS Stylesheet**:
You can create a separate CSS file, write styles for your component, and import the CSS file into your component file.

```jsx
/* styles.css */
.my-button {
  background-color: blue;
  color: white;
}
```jsx
import './styles.css';
return <button className="my-button">Click Me</button>;
```
4. **CSS Modules**:
With CSS Modules, you can create scoped styles that only apply to the component that imports them. You define the styles in a .module.css file and import them in the component.

```jsx
/* styles.module.css */
.button {
  background-color: red;
  padding: 10px;
}
```
```jsx

import styles from './styles.module.css';
return <button className={styles.button}>Click Me</button>;
```

## Techniques to Optimize React App Performance:

Here are several techniques to optimize the performance of a React app:

Minimize API Calls & Use CDN for Images:
Reduce unnecessary network requests and use Content Delivery Networks (CDNs) for faster image loading.

Using useMemo():
useMemo() is a React hook that caches the result of expensive functions and re-calculates them only when necessary, helping avoid redundant computations during re-renders.

```jsx

const memoizedValue = useMemo(() => expensiveFunction(data), [data]);
```

Using React.PureComponent:
React.PureComponent is a base class for components that implements shouldComponentUpdate() with a shallow prop and state comparison. It can help reduce unnecessary re-renders in class components.

```jsx
class MyComponent extends React.PureComponent { ... }
```

Maintaining State Colocation:
Colocate state by keeping it as close as possible to the component that needs it. This minimizes unnecessary re-renders in parent components.

```jsx
// Instead of keeping state in the parent, move it to the relevant child component
const ChildComponent = () => {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(count + 1)}>{count}</button>;
};
```

Lazy Loading:
Lazy loading reduces the initial load time of your React app by loading components only when needed, rather than all at once.

```jsx
const LazyComponent = React.lazy(() => import('./LazyComponent'));
```

## What are Higher Order Components (HOCs)?
A Higher-Order Component (HOC) is a function that takes a component and returns a new component with enhanced functionality. HOCs allow you to reuse logic across components without repeating code.

## When do we need a Higher-Order Component?

HOCs are useful when you need to reuse component logic across multiple components, especially if the components are similar but differ in specific ways.
Instead of duplicating logic in each component, an HOC abstracts the shared functionality into a single place, making the code more DRY (Don't Repeat Yourself).
Example of a Higher-Order Component:
```jsx
function withLogging(WrappedComponent) {
  return function(props) {
    console.log('Component rendered');
    return <WrappedComponent {...props} />;
  };
}
const MyComponent = () => <div>My Component</div>;
const MyComponentWithLogging = withLogging(MyComponent);
```
In this example, withLogging is a higher-order component that logs a message each time MyComponent renders. The HOC enhances the original component's behavior.
