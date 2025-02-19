# Javascript

## What is JavaScript?

JavaScript is a high-level, dynamic, and interpreted programming language primarily used for building interactive and dynamic websites. 

It is an essential part of modern web development, allowing developers to create rich, interactive user interfaces, handle events, and perform real-time updates on web pages without requiring the page to reload.

## Call, Apply and Bind

1. **call() Method:**

The call() method allows you to call a function with a specified 'this' value and an individual arguments passed to the function.

**Syntax:**

```bash
func.call(thisArg, arg1, arg2, ...)
thisArg: The value to use as this when calling the function.
arg1, arg2, ...: The arguments you want to pass to the function.
```

**Example:**

```bash
const person = {
  firstName: "John",
  lastName: "Doe"
};

function fullName(city, country) {
  console.log(this.firstName + " " + this.lastName + " from " + city + ", " + country);
}

fullName.call(person, "New York", "USA");
// Output: John Doe from New York, USA
```

In this case, call() is used to set the this value to the person object, and then the function is invoked with two arguments "New York" and "USA".

2. **apply() Method:**
The apply() method is similar to call(), but instead of passing arguments individually, you pass them as an array (or array-like object).

**Syntax:**

```bash
func.apply(thisArg, [arg1, arg2, ...])
thisArg: The value to use as this when calling the function.
[arg1, arg2, ...]: An array or array-like object containing the arguments.
```

**Example:**

```bash
const person = {
  firstName: "Jane",
  lastName: "Doe"
};

function fullName(city, country) {
  console.log(this.firstName + " " + this.lastName + " from " + city + ", " + country);
}

fullName.apply(person, ["Los Angeles", "USA"]);
// Output: Jane Doe from Los Angeles, USA
```

Here, apply() is used to set this to person and pass the arguments in an array ["Los Angeles", "USA"].

3. **bind() Method**
The bind() method returns a new function that, when called, has its this value set to the provided thisArg. Unlike call() and apply(), which immediately invoke the function, bind() does not invoke the function right away—it returns a new function that you can invoke later with the correct this value.

**Syntax:**

```bash
const newFunc = func.bind(thisArg, arg1, arg2, ...)
thisArg: The value to use as this when calling the new function.
arg1, arg2, ...: Arguments that will be pre-set in the new function.
```

**Example:**

```bash
const person = {
  firstName: "Alice",
  lastName: "Smith"
};

function fullName(city, country) {
  console.log(this.firstName + " " + this.lastName + " from " + city + ", " + country);
}

const boundFullName = fullName.bind(person, "London");
// Now `boundFullName` has `this` set to `person` and "London" as the first argument

boundFullName("England");
// Output: Alice Smith from London, England
```

In this case, bind() is used to create a new function (boundFullName) with this set to person and the first argument "London" pre-filled. The second argument "England" is passed when calling boundFullName() later.

https://www.youtube.com/watch?v=75W8UPQ5l7k&t=330s

## this keyword difference in normal vs arrow function

**1. Normal Functions:**

- In a normal function, the value of this is determined by how the function is called (its execution context).

- When a normal function is called as a method on an object, this refers to the object. If the function is called in a standalone manner, this refers to the global object (in non-strict mode) or undefined (in strict mode).

**Example:**

```bash
const person = {
  name: "Alice",
  greet: function() {
    console.log(this.name);  // `this` refers to `person`
  }
};

person.greet();  // Output: Alice

const greet = person.greet;
greet();  // In non-strict mode, this refers to the global object; in strict mode, it refers to undefined
```

**2. Arrow Functions:**

- Arrow functions don't have their own this value. Instead, they lexically bind this, meaning the value of this is inherited from the surrounding context in which the arrow function is defined. This is often referred to as "lexical scoping."

- In an arrow function, this will refer to the same value of this as it does in the scope where the arrow function is defined, not how it’s invoked.

**Example:**

```bash
const person = {
  name: "Bob",
  greet: () => {
    console.log(this.name);  // `this` does NOT refer to `person`, but to the global context
  }
};

person.greet();  // In non-strict mode, `this` refers to the global object (e.g., `window` in a browser)

const greet = person.greet;
greet();  // Still does not work as expected because `this` is bound lexically, not to `person`
```

## What is Hoisting?

Hoisting is a JavaScript behavior where variable and function declarations are moved (“hoisted”) to the top of their containing scope during compilation. This means you can use variables and functions before they are declared in the code.

**Hoisting in Functions**
Function declarations are fully hoisted, meaning they can be called before they appear in the code.
```jsx
sayHello(); // Works fine
function sayHello() {
  console.log("Hello, world!");
}
```
**Hoisting in Variables**
Variable declarations are hoisted, but their values are not initialized. Variables declared with var are hoisted with an undefined value, while let and const remain uninitialized (temporal dead zone).

```jsx
console.log(x); // undefined
var x = 5;
console.log(x); // 5
```

However, let and const behave differently:
```jsx
console.log(y); // ReferenceError: Cannot access 'y' before initialization
let y = 10;
```
## 1. Can you explain how JavaScript handles asynchronous operations?

JavaScript is a programming language capable of handling asynchronous operations efficiently. There are various methods through which JavaScript handles asynchronous operations such as callbacks, promises, and async/await.


### Callback:
A callback is a function passed as an argument to another function and is intended to be executed later, usually after the completion of an asynchronous operation or a specific event.
```bash

function fetchData(callback) {
    setTimeout(() => {
        console.log("Data fetched");
        callback();
    }, 1000);
}
function onComplete() {
    console.log("Callback executed!");
}
fetchData(onComplete)
```

### Promises: 

Promise represents the eventual completion (or failure) of an asynchronous operation and its resulting value. 

Promises have three states:

- Pending: The operation is still ongoing.
- Fulfilled (Resolved): The operation completed successfully, and the result is available.
- Rejected: The operation failed, and an error occurred.

```bash
function fetchData() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      let data = { name: "John", age: 30 };
      resolve(data); // Simulating a successful data fetch
    }, 2000);
  });
}

fetchData()
  .then((data) => {
    console.log("Data received:", data);
  })
  .catch((error) => {
    console.error("Error:", error);
  });
```
### Async/Await: 

Async/await is a newer syntactic sugar introduced in ECMAScript 2017 that simplifies the process of writing asynchronous code in JavaScript. 
It is built on top of promises and provides a more concise and readable syntax for handling asynchronous operations. 

Async/await lets engineers write asynchronous code that looks and behaves like synchronous code, making it easier to understand and maintain.

In summary, JavaScript provides various methods for handling asynchronous operations, including callbacks, promises, and async/await. 
Each method has its own advantages and disadvantages, and developers can choose the method suitable for their needs to write efficient and effective asynchronous code.

## 2.  Can you explain closures in JavaScript?

In JavaScript, a closure is a function that has the ability to access its own scope, as well as the scopes of the functions that surround it and the global scope. 
This feature allows functions to remember and access variables from an outer function even after the outer function has been executed.

The outer function's variables and parameters are then accessible within the inner function, even after the outer function has finished running.

A closure in JavaScript is a powerful concept that occurs when a function retains access to its lexical scope (the scope in which it was created) even after that scope has finished executing. In other words, a closure allows a function to "remember" the environment in which it was created, including the variables that were in scope at the time.

 However, it's also important to be aware of potential memory leaks and unintended consequences that can arise from improper use of closures.

 ## 3. How does JavaScript's event loop work?

 In JavaScript, an event loop is a mechanism used for managing asynchronous operations and executing callbacks non-blocking. It is a single-threaded loop that continuously monitors the call stack and the callback queue.

The call stack is a data structure that tracks the execution of functions in JavaScript. Whenever a function is invoked, it is pushed onto the call stack. When the function completes its execution, it is popped off the stack.

On the other hand, the callback queue holds a list of functions ready to be realized once the call stack is empty. 
Whenever an asynchronous operation, such as an event listener or a network request, completes its execution, its associated callback function is pushed into the callback queue.

When the call stack is empty, the event loop takes the first function from the callback queue, pushing it to the call stack, which effectively runs it. 
This process continues indefinitely, with the event loop continuously monitoring both the call stack and the callback queue to ensure that JavaScript code is executed in a non-blocking and efficient way.

## 4. Can you explain how prototypal inheritance works in JavaScript?

JavaScript is an object-oriented programming language. In JavaScript, every object has a prototype object that acts as a template object that it inherits methods and properties from. 
An object's prototype object may also have a prototype object from which it inherits methods and properties, creating a chain of prototypes. This chain of prototypes is called the prototype chain. 
The prototype chain allows objects to inherit properties and methods from their ancestors, which can be useful for code reuse and efficiency. By using the prototype chain, you can avoid duplication of code and create more efficient and maintainable code.

## 5. What is the purpose of JavaScript's "this" keyword?

The "this" keyword is used to refer to the object that it belongs to. The value of "this" varies depending on the context in which it is used. For instance, when used inside a method, "this" refers to the object that the method is called on. 
When used alone, "this" refers to the global object. Similarly, when used inside a function, "this" also refers to the global object. 
On the other hand, when used inside an event, "this" refers to the element receiving the event. It is important to note that the value of "this" is determined at runtime and depends on the way in which the function or method is called.

## 6. Can you explain how hoisting works in JavaScript?

In JavaScript, hoisting is a mechanism that rearranges the order in which variables and function declarations are processed during the compilation phase. The process involves moving the declarations to the top of their containing scope, which makes them available for use before their actual placement in the code. It's important to note that only the declarations are hoisted, and not their initializations. 
This means that variables and functions can be referenced before they are declared, but any assignments or function expressions that include them must come after their declaration.

## 7. Describe the difference between a method and a function in JavaScript

The function is a block of code designed to perform a particular task. A function is executed when something invokes it (calls it).

A method, on the other hand, is a function of an object. Methods get defined the way normal functions are defined, but they have to be assigned as the property of an object. 
Methods are typically used to update an object's properties or perform operations based on an object's current properties.

## 8. Can you explain the concept of promises in JavaScript?

In JavaScript, a Promise is a special object representing an asynchronous operation's eventual completion or failure. It's like a placeholder for the outcome of the operation. Every Promise can be in one of three states: pending, fulfilled, and rejected.

When a Promise is pending, the asynchronous operation is not yet completed, and the final result is unknown. Once the operation completes successfully, the Promise transitions to the fulfilled state, and the final result is available. 
If the operation fails for an error or some other reason, the Promise transitions to the rejected state, and the reason for the failure is available.

Promises are incredibly useful in JavaScript because they let developers write cleaner and more efficient code for handling asynchronous operations. You can chain multiple asynchronous operations, handle errors gracefully, and simplify your code.

## 9. What is the difference between asynchronous and synchronous programming in JavaScript?

Synchronous programming, also known as blocking programming, is a programming model where the code is executed sequentially from top-to-bottom, meaning that the next operation is blocked until the current one completes. 
This means that the program's execution is halted until the current operation is completed, and only then can the next operation be executed. 
This approach can be useful for simple programs that require a linear execution flow, but it can become problematic when dealing with more complex programs.

On the other hand, asynchronous programming is a programming model where the engine runs in an event loop. When an operation blocking is needed, the request starts, and the code keeps running without blocking for the result. 
This means that the program can continue to execute while waiting for the result of the operation. When the response is ready, the interrupt is fired, causing an event handler to be run, where the control flow continues. 
This approach helps reach a more efficient use of resources and can be particularly useful when dealing with long-running operations or when working with network I/O. 
However, it also requires a more complex programming model and can be difficult to understand and debug.

## 10. Explain event delegation in JavaScript?

Delegation of an event is the process where you delegate listening for events to a parent element. This allows you to listen for events that are fired on dynamically added elements or prevent the need for adding and removing event listeners when nodes are updated.

The principle behind event delegation is event bubbling. When an event occurs on a DOM element, that event is not entirely contained to that one element. 
After the event has been handled, it "bubbles" up to the element's parent, and the parent's parent, and so on, until it reaches the document object.

## 11. Can you explain the concept of functional programming and how it's applied in JavaScript?

Functional programming is a type of software engineering where programs are constructed with the application of functions. It avoids changing state and mutable data. 
In JavaScript, we can apply functional programming concepts using functions as first-class objects, higher-order functions, and pure functions.

## 12. Describe the difference between an arrow function and a regular function in JavaScript

Arrow functions and regular functions in JavaScript differ in several ways:

Syntax: Arrow functions have a shorter syntax than regular functions. You can omit the `function` keyword, the `return` keyword (for single-line blocks), and the curly brackets (for single-line blocks).
    "this" keyword: In regular functions, the `this` keyword shows the object that is called the function, which could be the document, the window or whatever. However, the `this` keyword doesn't bind its value in arrow functions. 
	It inherits it from the enclosing lexical context. This makes it easier to predict its behavior.
    Arguments object: Regular functions have their own `arguments` object. On the other hand, arrow functions do not have their own `arguments` object. Instead, you can use rest parameters to achieve similar functionality.
    Constructors: Regular functions created using the `function` declaration can be used as constructors (i.e., you can use the `new` keyword with them). Arrow functions, however, cannot be used as constructors. 
	If you try to use the `new` keyword with an arrow function, it will show an error.

 Prototype property: Regular functions have a prototype property, but arrow functions do not have this property.
 
 Method definitions: If you're defining methods within an object literal, you'll typically want to use regular function syntax for the method definition, as it makes the `this` keyword behave as expected.
	
## 13. Describe the purpose of the spread operator in JavaScript

The spread operator in JavaScript is used to spread the elements of an array (or any iterable) into places where zero or more elements are expected, or to spread the properties of an object into a new object.

## 14. Explain memoization in JavaScript

Memoization is a type of optimization technique used in computer programming to enhance the speed of programs. It works by storing the results of expensive function calls and reusing them whenever the same inputs occur again. 
By doing so, the program avoids repeating the same calculations and saves time by retrieving the result from the cache. 
This technique is useful in situations where the program has to perform complex calculations or repeatedly execute the same function with the same inputs. 
By using memoization, the program can reduce the time and resources needed to execute the code, making it more efficient and faster.

## 15. Describe the difference between a static method and an instance method in JavaScript

A static method is a method that's bound to the class, not an instance of the class. It's called on the class itself, not on instances. On the other hand, an instance method is available on an instance of a class, not on the class itself.

## 16. Explain the concept of data binding in JavaScript

Data binding in JavaScript is data synchronization between the model and view. The model and view are linked to allow automatic data synchronization between the model and view.

## 17. What is the difference between a JavaScript expression and a statement?

In JavaScript, an expression is any valid set of literals, variables, operators, and expressions that evaluates to a single value. A statement, on the other hand, acts. It could, for example, declare a variable or make a function call.

## 18. Can you explain the concept of immutability in JavaScript?

Immutability in JavaScript means that it can't be changed once a value is created. This is particularly useful in functional programming and can help to avoid side effects and make your code more predictable.

## 19. Can you explain the concept of strict mode in JavaScript?

In JavaScript, a specialized mode called "strict mode" enforces a stricter set of rules and restrictions on the code. It can be considered a "safer" version of JavaScript that helps developers avoid common mistakes and improve code quality. 
When strict mode is enabled, several silent errors that normally go unnoticed in regular JavaScript are caught and turned into thrown errors, making debugging much easier.

Additionally, strict mode fixes certain coding mistakes that can hinder JavaScript engine optimizations, improving performance. 
Finally, strict mode prohibits certain syntax and behaviors likely to be deprecated or removed in future versions of ECMAScript, thus helping ensure that your code remains future-proof. 
The strict mode is useful for developers who want to write high-quality, optimized, and future-proof JavaScript code.

## 20. What is the purpose of the JavaScript's Set object?

The JavaScript Set object is a collection of unique values. Values in a Set can be iterated in insertion order, and can only be added once; subsequent attempts to add the same value are ignored.

## 21.What is the difference between innerHTML & innerText? 

The innerText property sets or returns the text content as plain text of the specified node, and all its descendants whereas the innerHTML property sets or returns the plain text or HTML contents in the elements. 
Unlike innerText, inner HTML lets you work with HTML rich text and doesn't automatically encode and decode text.

## 22. What is an event bubbling in JavaScript?

Consider a situation an element is present inside another element and both of them handle an event. When an event occurs in bubbling, the innermost element handles the event first, then the outer, and so on.



