# Node.js Interview Questions & Answers 🚀  

A comprehensive list of the most important **Node.js** interview questions with examples.  

## Table of Contents  
- [What is Node.js?](#what-is-nodejs)  
- [How do you install Node.js?](#how-do-you-install-nodejs)  
- [What is the difference between CommonJS and ES Modules?](#what-is-the-difference-between-commonjs-and-es-modules)  
- [How do you create a simple server using Node.js?](#how-do-you-create-a-simple-server-using-nodejs)  
- [What is the Event Loop in Node.js?](#what-is-the-event-loop-in-nodejs)  
- [What are Streams in Node.js?](#what-are-streams-in-nodejs)  
- [What is Middleware in Express.js?](#what-is-middleware-in-expressjs)  
- [How does Node.js handle asynchronous operations?](#how-does-nodejs-handle-asynchronous-operations)  
- [What are Buffers in Node.js?](#what-are-buffers-in-nodejs)  
- [How do you handle file operations in Node.js?](#how-do-you-handle-file-operations-in-nodejs)  
- [What is a Package.json file?](#what-is-a-packagejson-file)  
- [How do you use environment variables in Node.js?](#how-do-you-use-environment-variables-in-nodejs)  

---

## What is Node.js?  
**Node.js** is a **JavaScript runtime** built on **Chrome’s V8 JavaScript engine**. It allows JavaScript to run **outside the browser**, making it suitable for **server-side** applications.  

### Key Features:  
- **Non-blocking I/O** model  
- **Event-driven architecture**  
- **Single-threaded but can handle multiple requests**  

---

## How do you install Node.js?  
Install **Node.js** via:  

1. Download from the official site: [https://nodejs.org](https://nodejs.org)  
2. Use a package manager:  
   - **macOS/Linux:**  
     ```sh
     brew install node
     ```  
   - **Windows:** Install via `.msi` installer  
   - **NVM (Node Version Manager):**  
     ```sh
     nvm install 18
     nvm use 18
     ```  

---

## What is the difference between CommonJS and ES Modules?  

### CommonJS (CJS) (Default in Node.js)  
- Uses `require()` and `module.exports`  
- Synchronous loading  

```js
// CommonJS
const fs = require('fs');
module.exports = { hello: "world" };
```  

### ES Modules (ESM) (`"type": "module"` in package.json)  
- Uses `import` and `export`  
- Asynchronous loading  

```js
// ES Modules
import fs from 'fs';
export const hello = "world";
```  

---

## How do you create a simple server using Node.js?  

```js
const http = require('http');

const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('Hello, Node.js Server!');
});

server.listen(3000, () => console.log('Server running on port 3000'));
```  
Run: `node server.js` and visit `http://localhost:3000`

---

## What is the Event Loop in Node.js?  

Node.js handles asynchronous operations via an **event loop**, allowing it to process multiple requests **without blocking**.  

### Example:  

```js
console.log('Start');

setTimeout(() => console.log('Timeout'), 0);
setImmediate(() => console.log('Immediate'));

console.log('End');
```  

### Output order:  
```
Start  
End  
Immediate  
Timeout  
```

---

## What are Streams in Node.js?  

Streams handle **large data** efficiently without loading everything into memory.  

### Example:  

```js
const fs = require('fs');

const readStream = fs.createReadStream('input.txt', 'utf8');
readStream.on('data', chunk => console.log(chunk));
```

---

## What is Middleware in Express.js?  

Middleware functions execute **before** sending a response in an Express app.  

```js
const express = require('express');
const app = express();

// Middleware function
app.use((req, res, next) => {
    console.log('Middleware executed');
    next();
});

app.get('/', (req, res) => res.send('Hello Express!'));

app.listen(3000, () => console.log('Server running on port 3000'));
```

---

## How does Node.js handle asynchronous operations?  

Node.js supports **asynchronous programming** using **Callbacks, Promises, and Async/Await**.  

### Example using Async/Await:  

```js
const fs = require('fs').promises;

async function readFile() {
    try {
        const data = await fs.readFile('file.txt', 'utf8');
        console.log(data);
    } catch (err) {
        console.error(err);
    }
}

readFile();
```

---

## What are Buffers in Node.js?  

Buffers are used to **handle binary data** directly.  

### Example:  

```js
const buffer = Buffer.from('Hello');
console.log(buffer); // <Buffer 48 65 6c 6c 6f>
console.log(buffer.toString()); // Hello
```

---

## How do you handle file operations in Node.js?  

Using the `fs` module:  

### Read a file:  

```js
const fs = require('fs');

fs.readFile('example.txt', 'utf8', (err, data) => {
    if (err) throw err;
    console.log(data);
});
```

### Write to a file:  

```js
fs.writeFile('output.txt', 'Hello, Node.js!', err => {
    if (err) throw err;
    console.log('File saved!');
});
```

---

## What is a Package.json file?  

`package.json` stores metadata about a Node.js project.  

### Example:  

```json
{
  "name": "nodejs-project",
  "version": "1.0.0",
  "dependencies": {
    "express": "^4.17.1"
  }
}
```

---

## How do you use environment variables in Node.js?  

Use the `process.env` object.  

### Steps:  
1. Create a `.env` file:  
   ```
   PORT=5000
   ```  
2. Install dotenv:  
   ```sh
   npm install dotenv
   ```  
3. Load `.env` variables:  
   ```js
   require('dotenv').config();
   console.log(process.env.PORT);
   ```

---

## Conclusion  
This covers **essential Node.js concepts** with examples. Feel free to contribute or suggest more questions!  

📌 **Star ⭐ this repo if it helped!**  