# React Interview Questions & Answers

### Why do we need a Framework?

Frameworks provide a structured and efficient way to build modern web applications. 
By using frameworks, developers can focus more on solving business problems rather than reinventing the wheel for common functionalities.

### Why React.js?

React.js is a flexible and efficient JavaScript library for building user interfaces. 
It uses a component-based architecture, enabling reusable and maintainable code, and a Virtual DOM for optimized rendering and better performance. 
Its declarative syntax simplifies UI development, while its large ecosystem and community provide extensive tools and resources. 
React is versatile, working seamlessly with libraries for state management (e.g., Redux) and routing, and it supports cross-platform development through tools like React Native. 
Backed by Facebook and widely used by major companies, React is a reliable choice for scalable, dynamic applications.

### What is JSX?
JSX is a XML-like syntax extension to ECMAScript (the acronym stands for JavaScript XML). Basically it just provides syntactic sugar for the React.createElement() function, giving us expressiveness of JavaScript along with HTML like template syntax.

In the example below text inside `<h1>` tag is returned as JavaScript function to the render function.
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


-----

1. Public/Manifest.json 
-> It help us to create PWA (Progressive web application)
-> The PWA technology allows the user to open a native-like app via a browser, install it instantly, make use of most native-like functions, and use the app offline.

2. Public/Robots.txt
-> Is used in SEO - Make website crawlable for search engine

3. node_modules folder 
-> Node module is a place which has the all the dependancy(javascript packages) which our project needs.

4. Webpack
-> npm run build -> start the react bundler and it uses webpack to bundle.

5. Hooks
-- use State
-- use Effect
-- use Context
-- use Reducer
-- use Memo
-- use Callback
-- use Ref

---

#### 1. `useEffect`:

**Answer:**
`useEffect` is a React Hook used for handling side effects in functional components. It allows us to perform actions in response to component mount, update, or unmount. This is particularly useful for tasks such as data fetching, subscriptions, or manual DOM manipulations.

**Example:**
```jsx
import React, { useEffect, useState } from 'react';

function ExampleComponent() {
  const [data, setData] = useState(null);

  useEffect(() => {
    // Perform side effect (e.g., fetch data)
    fetchData().then((result) => setData(result));

    // Cleanup function (optional)
    return () => {
      // Perform cleanup if needed
    };
  }, []); // Empty dependency array means it runs once on mount

  return (
    <div>
      {/* Render component using fetched data */}
      {data && <p>{data}</p>}
    </div>
  );
}
```

#### 2. `useState`:

**Answer:**
`useState` is a Hook that allows functional components to manage local state. It returns an array with the current state value and a function to update it. This enables us to handle state within functional components, replacing the need for class components.

**Example:**
```jsx
import React, { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
    </div>
  );
}
```

#### 3. `useContext`:

**Answer:**
`useContext` is a Hook that allows components to consume values from a React context without introducing a consumer component. It simplifies the process of passing data down through component trees.

**Example:**
```jsx
import React, { useContext } from 'react';

const MyContext = React.createContext();

function MyComponent() {
  const contextValue = useContext(MyContext);

  return (
    <div>
      <p>Value from context: {contextValue}</p>
    </div>
  );
}
```

#### 4. `useReducer`:

**Answer:**
`useReducer` is a Hook used for managing more complex state logic. It is preferable when the next state depends on the previous one and when the logic is more intricate than what `useState` can handle.

**Example:**
```jsx
import React, { useReducer } from 'react';

const initialState = { count: 0 };

function reducer(state, action) {
  switch (action.type) {
    case 'increment':
      return { count: state.count + 1 };
    default:
      return state;
  }
}

function Counter() {
  const [state, dispatch] = useReducer(reducer, initialState);

  return (
    <div>
      <p>Count: {state.count}</p>
      <button onClick={() => dispatch({ type: 'increment' })}>Increment</button>
    </div>
  );
}
```

#### 5. `useMemo`:

**Answer:**
`useMemo` is a Hook that memoizes the result of a computation. It helps in optimizing performance by preventing unnecessary re-computations.

**Example:**
```jsx
import React, { useMemo } from 'react';

function ExpensiveComponent({ data }) {
  const expensiveResult = useMemo(() => computeExpensiveResult(data), [data]);

  return (
    <div>
      <p>Result: {expensiveResult}</p>
    </div>
  );
}
```

#### 6. `useCallback`:

**Answer:**
`useCallback` is a Hook that memoizes callback functions. It is useful when passing callbacks to child components to prevent unnecessary re-renders.

**Example:**
```jsx
import React, { useState, useCallback } from 'react';

function ParentComponent() {
  const [count, setCount] = useState(0);

  const handleClick = useCallback(() => {
    setCount(count + 1);
  }, [count]);

  return (
    <div>
      <ChildComponent onClick={handleClick} />
    </div>
  );
}

function ChildComponent({ onClick }) {
  return <button onClick={onClick}>Click me</button>;
}
```

#### 7. `useRef`:

**Answer:**
`useRef` is a Hook that provides a mutable object whose `.current` property is initialized with the passed argument (initial value). It persists across renders and is commonly used to access and interact with the DOM.

**Example:**
```jsx
import React, { useRef, useEffect } from 'react';

function InputWithFocus() {
  const inputRef = useRef();

  useEffect(() => {
    // Focus the input element on mount
    inputRef.current.focus();
  }, []);

  return <input ref={inputRef} />;
}
```

---


6. Custom Hooks
-- What?
-- Why?
-- When?
-- How?

#### 1. What are Custom Hooks?

**Definition:**
Custom Hooks are a feature in React that allows you to extract and reuse logic from functional components. They are functions whose names typically start with "use" and can contain stateful logic, side effects, or other custom behavior.

#### 2. Why use Custom Hooks?

**Benefits:**
- **Reuse:** Custom Hooks promote code reuse by encapsulating logic that can be shared across different components.
- **Abstraction:** They help in abstracting complex logic, making components cleaner and more focused on their specific responsibilities.
- **Readability:** Custom Hooks enhance code readability by separating concerns and making the component's purpose clearer.
- **Testing:** Logic encapsulated in custom hooks can be easily tested independently, promoting better testability.

#### 3. When to use Custom Hooks?

**Use Cases:**
- **Shared Logic:** When multiple components share similar logic, it's a good candidate for extraction into a custom hook.
- **Complex State Management:** For components with complex state management or side effects, custom hooks can simplify the component code.
- **Abstraction:** When a component becomes too cluttered with various concerns, extracting related logic into a custom hook improves maintainability.

#### 4. How to create Custom Hooks?

**Steps:**
1. **Create a Function:** Define a function with a name that starts with "use" to indicate it's a hook.
2. **Logic Extraction:** Move the logic you want to reuse from your component into the custom hook.
3. **Hook Signature:** Decide what parameters your hook will accept, and what values or functions it will return.
4. **Usage of Existing Hooks:** Leverage existing React hooks if needed within your custom hook.
5. **Return Values:** Ensure that your custom hook returns values or functions needed by the component.
6. **Example:**
   ```jsx
   import { useState, useEffect } from 'react';

   function useFetchData(url) {
     const [data, setData] = useState(null);
     const [loading, setLoading] = useState(true);

     useEffect(() => {
       const fetchData = async () => {
         try {
           const response = await fetch(url);
           const result = await response.json();
           setData(result);
         } catch (error) {
           console.error('Error fetching data:', error);
         } finally {
           setLoading(false);
         }
       };

       fetchData();
     }, [url]);

     return { data, loading };
   }
   ```

#### 5. Example Usage:

**Using the Custom Hook:**
```jsx
import React from 'react';
import useFetchData from './useFetchData';

function DataComponent() {
  const { data, loading } = useFetchData('https://api.example.com/data');

  return (
    <div>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <ul>
          {data.map((item) => (
            <li key={item.id}>{item.name}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

In this example, the custom hook `useFetchData` encapsulates the logic for fetching data, providing a clean and reusable solution for components needing similar functionality.


7. Higher Order components
-- What?
-- Why?
-- When?
-- How?

#### 1. What are Higher Order Components?

**Definition:**
A Higher Order Component (HOC) is a design pattern in React that involves taking a component and wrapping it in a function to enhance its functionality. The function takes a component as an argument and returns a new component with additional features, props, or behavior.

#### 2. Why use Higher Order Components?

**Benefits:**
- **Reusability:** HOCs allow the reuse of component logic across different parts of the application.
- **Abstraction:** They promote the abstraction of common functionalities, keeping components focused on their core responsibilities.
- **Composition:** HOCs enable the composition of behaviors by combining multiple HOCs to create a higher-level component.
- **Separation of Concerns:** Enhances the separation of concerns by isolating specific functionalities into independent HOCs.

#### 3. When to use Higher Order Components?

**Use Cases:**
- **Cross-Cutting Concerns:** When multiple components share common logic or behavior (e.g., authentication, logging).
- **Props Manipulation:** When you need to inject additional props into a component.
- **Conditional Rendering:** To conditionally render a component based on certain criteria.
- **Code Organization:** When you want to keep your components more focused and modular.

#### 4. How to create Higher Order Components?

**Steps:**
1. **Create a Function:** Define a function that takes a component as an argument.
2. **Component Wrapper:** Inside the function, return a new component that wraps the original one.
3. **Manipulate Props:** Optionally, manipulate or add props before passing them to the wrapped component.
4. **Example:**
   ```jsx
   import React from 'react';

   const withAuthentication = (WrappedComponent) => {
     class WithAuthentication extends React.Component {
       // Additional logic for authentication

       render() {
         return <WrappedComponent {...this.props} />;
       }
     }

     return WithAuthentication;
   };
   ```

#### 5. Example Usage:

**Using the Higher Order Component:**
```jsx
import React from 'react';
import withAuthentication from './withAuthentication';

class AuthenticatedComponent extends React.Component {
  render() {
    return <p>User is authenticated!</p>;
  }
}

const EnhancedComponent = withAuthentication(AuthenticatedComponent);

// Render EnhancedComponent somewhere in your application
```

In this example, `withAuthentication` is a Higher Order Component that adds authentication logic to the `AuthenticatedComponent`. The result is a new component (`EnhancedComponent`) with enhanced functionality.

HOCs provide a powerful way to share functionality among components, making them a key aspect of code reuse and organization in React applications. However, with the introduction of Hooks and render props, developers now have alternative patterns for achieving similar goals. The choice between HOCs and other patterns depends on the specific requirements and preferences of the project.


8. Life Cycle method of components
-- Call components sequence

### Mounting Phase:

1. **`constructor(props)`**
   - The constructor is called when an instance of the component is being created.
   - It is used for initializing state, binding event handlers, and other setup tasks.

2. **`static getDerivedStateFromProps(props, state)`**
   - This static method is called right before rendering when new props or state are received.
   - It returns an object to update the state or `null` if no state update is needed.

3. **`render()`**
   - The `render` method is responsible for rendering the component and returning the JSX.
   - It should be a pure function without side effects.

4. **`componentDidMount()`**
   - `componentDidMount` is invoked immediately after a component is inserted into the DOM.
   - It is a good place to initiate network requests, set up subscriptions, or perform other side effects.

### Updating Phase:

5. **`static getDerivedStateFromProps(nextProps, nextState)`**
   - Similar to the mounting phase, this static method is called before rendering during an update.

6. **`shouldComponentUpdate(nextProps, nextState)`**
   - This method is called before rendering when new props or state are received.
   - It returns a boolean to determine whether the component should re-render.

7. **`render()`**
   - The `render` method is called again to update the UI based on new props or state.

8. **`getSnapshotBeforeUpdate(prevProps, prevState)`**
   - This method is called right before the changes from `render` are reflected in the DOM.
   - It allows you to capture information, such as scroll position, before the update.

9. **`componentDidUpdate(prevProps, prevState, snapshot)`**
   - `componentDidUpdate` is invoked immediately after the component is re-rendered.
   - It is a good place to perform side effects, like network requests based on props changes.

### Unmounting Phase:

10. **`componentWillUnmount()`**
    - `componentWillUnmount` is called just before a component is removed from the DOM.
    - It is used to perform cleanup, such as cancelling network requests or cleaning up subscriptions.

### Error Handling:

11. **`static getDerivedStateFromError(error)`**
    - This static method is called when there is an error during rendering.
    - It allows the component to render a fallback UI.

12. **`componentDidCatch(error, info)`**
    - `componentDidCatch` is called after an error has been thrown during rendering.
    - It is used for logging the error or performing other error-handling actions.

**Note:** Some lifecycle methods are considered legacy, and their usage is discouraged in newer React versions. These include `componentWillMount`, `componentWillReceiveProps`, and `componentWillUpdate`. Developers are encouraged to use the static methods and Hooks introduced in React 16.3 and later for better code organization.

Understanding the React component lifecycle is crucial for effective development and debugging. Keep in mind that with the introduction of Hooks in React 16.8, functional components now have access to lifecycle methods through hooks like `useEffect`. Hooks provide a more concise and flexible way to manage component lifecycle in functional components.


9. State Management
-- State / Props
-- Props driling
-- context

### State/Props

#### State:
- **Definition:** The state is a data structure that represents the internal state of a React component. It can be mutable and is managed within the component.
- **Usage:**
  ```jsx
  import React, { useState } from 'react';

  function Counter() {
    const [count, setCount] = useState(0);

    return (
      <div>
        <p>Count: {count}</p>
        <button onClick={() => setCount(count + 1)}>Increment</button>
      </div>
    );
  }
  ```

#### Props:
- **Definition:** Props (short for "properties") are data passed from a parent component to a child component. Props are immutable and provide a way to customize the behavior of child components.
- **Usage:**
  ```jsx
  import React from 'react';

  function Greet(props) {
    return <p>Hello, {props.name}!</p>;
  }

  function App() {
    return <Greet name="John" />;
  }
  ```

### Props Drilling

#### Definition:
Props drilling refers to the process of passing down props through multiple layers of nested components, even if some intermediary components do not directly use those props. This can lead to verbose code and potential maintenance issues.

#### Example:

```jsx
// ParentComponent.jsx
import React, { useState } from 'react';
import ChildComponent from './ChildComponent';

function ParentComponent() {
  const [data, setData] = useState('Hello from parent!');

  return <ChildComponent data={data} />;
}

// ChildComponent.jsx
import React from 'react';
import GrandchildComponent from './GrandchildComponent';

function ChildComponent({ data }) {
  return <GrandchildComponent data={data} />;
}

// GrandchildComponent.jsx
import React from 'react';

function GrandchildComponent({ data }) {
  return <p>{data}</p>;
}
```

In this example, `ParentComponent` passes the `data` prop down to `ChildComponent`, which then passes it down to `GrandchildComponent`. This is prop drilling, and it can become cumbersome as the application grows.

### Context

#### Definition:
Context in React provides a way to share values like themes, user authentication, or other global settings without explicitly passing them through props at every level of the component tree.

#### Example:

```jsx
// MyContext.js
import { createContext } from 'react';

const MyContext = createContext();

export default MyContext;

// ParentComponent.jsx
import React, { useContext } from 'react';
import MyContext from './MyContext';
import ChildComponent from './ChildComponent';

function ParentComponent() {
  const data = 'Hello from context!';
  
  return (
    <MyContext.Provider value={data}>
      <ChildComponent />
    </MyContext.Provider>
  );
}

// ChildComponent.jsx
import React, { useContext } from 'react';
import MyContext from './MyContext';
import GrandchildComponent from './GrandchildComponent';

function ChildComponent() {
  const data = useContext(MyContext);
  
  return <GrandchildComponent data={data} />;
}

// GrandchildComponent.jsx
import React from 'react';

function GrandchildComponent({ data }) {
  return <p>{data}</p>;
}
```

In this example, the `ParentComponent` provides the `data` value through the `MyContext.Provider`, and both `ChildComponent` and `GrandchildComponent` consume this value using the `useContext` hook. Context eliminates the need for prop drilling in scenarios where multiple components need access to the same data.


10. Redux / Zustand
-- What?
-- Why?
-- When?
-- How?
-- RTK - Redux toolkit


11. Lazy Loading
-- Code spliting
-- Code chunking
-- Suspense

### Lazy Loading

#### Definition:
Lazy loading is a technique in software development where a feature or module is loaded only when it is actually needed. In the context of React applications, this often involves deferring the loading of components until they are about to be rendered.

#### Example:

```jsx
import React, { lazy, Suspense } from 'react';

const LazyComponent = lazy(() => import('./LazyComponent'));

function App() {
  return (
    <div>
      <Suspense fallback={<div>Loading...</div>}>
        <LazyComponent />
      </Suspense>
    </div>
  );
}
```

In this example, the `LazyComponent` is loaded lazily using the `lazy` function and the dynamic `import` statement. The `Suspense` component provides a fallback UI to be displayed while the lazy component is being loaded.

### Code Splitting

#### Definition:
Code splitting is a technique to divide a JavaScript bundle into smaller, more manageable chunks. By splitting the code into smaller pieces, you can load only the necessary parts of your application when they are needed, reducing the initial load time.

#### Example:

```jsx
import React, { Component } from 'react';

class App extends Component {
  handleClick = async () => {
    const module = await import('./DynamicModule');
    module.default();
  };

  render() {
    return (
      <div>
        <button onClick={this.handleClick}>Load Dynamic Module</button>
      </div>
    );
  }
}

export default App;
```

In this example, the `DynamicModule` is dynamically imported when the button is clicked, allowing it to be loaded on-demand instead of being included in the main bundle.

### Code Chunking

#### Definition:
Code chunking is the process of breaking down a codebase into smaller, independently loadable chunks. Each chunk contains a portion of the application's code, and these chunks can be loaded on-demand, enhancing performance by reducing the initial loading time.

#### Example:

```jsx
// webpack.config.js
module.exports = {
  entry: {
    main: './src/index.js',
    vendor: './src/vendor.js',
  },
  optimization: {
    splitChunks: {
      chunks: 'all',
    },
  },
};
```

In this example, using webpack's `splitChunks` optimization, the code is split into separate chunks for the `main` application and `vendor` dependencies. This allows for more efficient loading, as the vendor code can be cached separately.

### Suspense

#### Definition:
Suspense is a React feature that enables components to suspend rendering while waiting for some asynchronous operation to complete, such as data fetching. It can be used in combination with lazy loading to handle loading states more elegantly.

#### Example:

```jsx
import React, { lazy, Suspense } from 'react';

const LazyComponent = lazy(() => import('./LazyComponent'));

function App() {
  return (
    <div>
      <Suspense fallback={<div>Loading...</div>}>
        <LazyComponent />
      </Suspense>
    </div>
  );
}
```

In this example, the `Suspense` component wraps the `LazyComponent`, providing a fallback UI to be displayed while the lazy component is being loaded. `Suspense` is a key tool for handling asynchronous operations in a more declarative and user-friendly manner.


12. Virtual Dom
-- Reconcilation
-- React Fiber
-- How component renders
-- Diffine Algo

### Virtual DOM

#### Definition:
The Virtual DOM (Document Object Model) is a lightweight, in-memory representation of the actual DOM elements in a web page. It is a concept used by React to improve performance by minimizing the number of direct manipulations to the actual DOM.

#### How It Works:
1. When a React component renders, it creates a virtual representation of the DOM elements.
2. Any changes to the component result in a new virtual DOM representation.
3. React compares the new virtual DOM with the previous one to identify the differences (diffing).
4. It calculates the most efficient way to update the actual DOM based on the differences.
5. Finally, React updates only the necessary parts of the real DOM to reflect the changes.

### Reconciliation

#### Definition:
Reconciliation is the process in React where it compares the new virtual DOM representation with the previous one and determines the minimal set of changes needed to update the actual DOM. This process ensures that the UI stays in sync with the application state efficiently.

#### How It Works:
1. React starts by comparing the root elements of the new and previous virtual DOM trees.
2. It then recursively compares child elements, identifying insertions, updates, or deletions.
3. React minimizes the number of DOM manipulations needed to reflect the changes.
4. Reconciliation is a key part of React's efficient rendering strategy, ensuring that updates are performed with minimal impact on performance.

### React Fiber

#### Definition:
React Fiber is a reimplementation of the React reconciliation algorithm. It is designed to improve the performance and responsiveness of React applications, especially in scenarios with frequent updates, such as animations, gestures, and large component trees.

#### How It Works:
1. React Fiber introduces a more granular approach to rendering, allowing interruptions and prioritization of certain tasks.
2. It enables the scheduler to pause, abort, or resume rendering tasks, improving the application's responsiveness.
3. Fiber allows React to work on rendering chunks of the virtual DOM, making it more efficient and responsive to user interactions.

### How Components Render

#### Component Rendering Process:
1. **Initialization:** When a component is created, its constructor is called, and the initial state is set.
2. **Mounting:** The `render` method is called, creating the initial virtual DOM representation. The resulting HTML is appended to the actual DOM.
3. **Updates:** When the component's state or props change, React schedules a re-render.
4. **Reconciliation:** React compares the new virtual DOM with the previous one, identifying changes.
5. **Diffing and Patching:** React calculates the minimal set of changes needed to update the actual DOM, minimizing performance impact.
6. **Component Lifecycle Hooks:** If defined, lifecycle hooks such as `componentDidUpdate` are called after the update is complete.

### Define Algorithm (Reconciliation/Diffing Algorithm)

#### Diffing Algorithm:
1. **Start at the Root:** Compare the new virtual DOM tree with the previous one, starting at the root.
2. **Identify Changes:** Recursively traverse the virtual DOM trees, identifying changes in elements, attributes, or text content.
3. **Update Strategy:** Determine the most efficient update strategy to minimize actual DOM manipulations.
4. **Recurse on Children:** Apply the diffing algorithm to child elements, continuing the process recursively.
5. **Keyed Elements:** When rendering lists, React uses keys to efficiently update elements based on their identity.

This algorithm ensures that React performs updates to the actual DOM in an optimized and minimal way, improving the overall performance of React applications. The reconciliation process is at the core of React's declarative and efficient rendering model.


13. SSR vs CSR
-- What?
-- Why?
-- When?
-- How?
-- Diff
-- SEO
-- Performing

14. Routing (RBAC)
-- React Router
-- protected routes
-- Query params
-- Dynamic Routing

### Routing in React (Role-Based Access Control - RBAC)

#### React Router

**Definition:**
React Router is a popular library for handling navigation and routing in React applications. It allows developers to define and navigate between different views or pages in a single-page application (SPA).

**Installation:**
```bash
npm install react-router-dom
```

**Basic Usage:**
```jsx
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';

function Home() {
  return <h2>Home</h2>;
}

function About() {
  return <h2>About</h2>;
}

function App() {
  return (
    <Router>
      <div>
        <nav>
          <ul>
            <li><Link to="/">Home</Link></li>
            <li><Link to="/about">About</Link></li>
          </ul>
        </nav>

        <Route path="/" exact component={Home} />
        <Route path="/about" component={About} />
      </div>
    </Router>
  );
}
```

#### Protected Routes

**Definition:**
Protected routes are routes that require authentication or specific user roles to access. In an RBAC context, certain routes may only be accessible to users with specific roles.

**Example:**
```jsx
import { Route, Redirect } from 'react-router-dom';

function PrivateRoute({ component: Component, isAuthenticated, ...rest }) {
  return (
    <Route
      {...rest}
      render={(props) =>
        isAuthenticated ? (
          <Component {...props} />
        ) : (
          <Redirect to="/login" />
        )
      }
    />
  );
}

// Usage
<PrivateRoute
  path="/dashboard"
  component={Dashboard}
  isAuthenticated={user.isAuthenticated}
/>
```

In this example, the `PrivateRoute` component checks if the user is authenticated. If authenticated, it renders the protected component; otherwise, it redirects to the login page.

#### Query Params

**Definition:**
Query parameters are key-value pairs attached to the end of a URL. They are used to pass data to a route.

**Example:**
```jsx
// URL: /search?q=react&page=1
const searchQuery = new URLSearchParams(window.location.search).get('q');
const page = new URLSearchParams(window.location.search).get('page');
```

In this example, the URL contains query parameters (`q=react` and `page=1`). You can use `URLSearchParams` to extract these parameters in a React component.

#### Dynamic Routing

**Definition:**
Dynamic routing involves defining routes with dynamic segments or parameters. These parameters can be used to create flexible and reusable route patterns.

**Example:**
```jsx
import { Route } from 'react-router-dom';

function UserProfile() {
  return <h2>User Profile</h2>;
}

function App() {
  return (
    <div>
      <Route path="/users/:userId" component={UserProfile} />
    </div>
  );
}
```

In this example, the `:userId` in the route pattern is a dynamic parameter. It matches any value and passes it as a prop to the `UserProfile` component.

Routing in React, especially when combined with RBAC, provides a powerful mechanism for navigating between different views and controlling access based on user roles. React Router is a widely used library for handling routing in React applications.


15. Testing
-- React Testing

16. Async Tasks
-- API calls
-- Events
-- Promises
-- set timeout 

### Async Tasks in JavaScript

#### API Calls

**Using `fetch`:**
```javascript
fetch('https://api.example.com/data')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error fetching data:', error));
```

**Using `async/await` (with `fetch`):**
```javascript
async function fetchData() {
  try {
    const response = await fetch('https://api.example.com/data');
    const data = await response.json();
    console.log(data);
  } catch (error) {
    console.error('Error fetching data:', error);
  }
}

fetchData();
```

#### Events

**Using Event Listeners:**
```javascript
const button = document.getElementById('myButton');

button.addEventListener('click', (event) => {
  console.log('Button clicked!', event);
});
```

**Using `async/await` with Promises (for asynchronous events):**
```javascript
const waitForClick = () => new Promise(resolve => {
  const handleClick = (event) => {
    resolve(event);
    button.removeEventListener('click', handleClick);
  };

  button.addEventListener('click', handleClick);
});

async function handleAsyncEvent() {
  const event = await waitForClick();
  console.log('Button clicked!', event);
}

handleAsyncEvent();
```

#### Promises

**Creating a Promise:**
```javascript
const myPromise = new Promise((resolve, reject) => {
  // Asynchronous operation, e.g., fetching data
  const data = fetchData();

  if (data) {
    resolve(data);
  } else {
    reject('Error fetching data');
  }
});

myPromise
  .then(data => console.log(data))
  .catch(error => console.error(error));
```

#### `setTimeout`

```javascript
console.log('Start');

setTimeout(() => {
  console.log('Timeout completed!');
}, 2000);

console.log('End');
```

In this example, the `setTimeout` function is used to delay the execution of the callback by 2000 milliseconds (2 seconds). The program continues executing the rest of the code without waiting for the timeout to complete.

### `async/await` with `setTimeout`

```javascript
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function example() {
  console.log('Start');
  await delay(2000);
  console.log('Timeout completed!');
  console.log('End');
}

example();
```

In this example, the `delay` function returns a promise that resolves after a specified number of milliseconds. The `async/await` syntax is used to make the asynchronous code appear more synchronous and readable.


17. use keywords like re-usable, modular, testable,  maintainable. 

18. Focus on the Performance (improve user expereince asset optimization(img, js, css, write optimized code), lazy loading, shimmer UI, optimazation at bundler level, CDN level, server level), rendering of componet faster

19. Styling  (pros and cons of using Tailwind over bootstrap vice versa and so on....) styleX, css/scss

20. Accessebility , security, performace, testability (these are the pillars of any application)


21. 




Q1. React Context API

