# Node.js Interview Preparation Guide

*25 questions with detailed answers — from fundamentals to advanced*

---

## Part 1: The Basics (Questions 1–10)

### 1. What is Node.js, and how does it differ from browser-based JavaScript?

Node.js is a JavaScript runtime built on Chrome's V8 engine that lets you run JavaScript outside the browser — primarily on servers.

**Key differences from browser JS:**

| | Browser JS | Node.js |
|---|---|---|
| **Environment** | Runs in the browser | Runs on the server/OS |
| **DOM Access** | Has `window`, `document` | No DOM — has `process`, `global` |
| **File System** | No direct file access (sandboxed) | Full file system access via `fs` |
| **Modules** | Historically `<script>` tags; now ES Modules | CommonJS (`require`) and ES Modules (`import`) |
| **Use Case** | UI rendering, DOM manipulation | APIs, file I/O, real-time apps, CLI tools |

**Sample answer:** *"Node.js takes the V8 engine out of the browser and wraps it with system-level APIs — file system, networking, child processes — so you can build server-side applications in JavaScript. Unlike the browser, there's no DOM, but you get access to things like `fs`, `http`, `net`, and `os`."*

---

### 2. What is the Event Loop, and how does it work in Node.js?

The event loop is the core mechanism that allows Node.js to perform non-blocking I/O despite being single-threaded. It continuously checks for and dispatches callbacks/events.

**Phases of the event loop (simplified):**

```
   ┌───────────────────────────┐
┌─>│         Timers             │  (setTimeout, setInterval callbacks)
│  └───────────┬───────────────┘
│  ┌───────────┴───────────────┐
│  │     Pending Callbacks      │  (I/O callbacks deferred to next loop)
│  └───────────┬───────────────┘
│  ┌───────────┴───────────────┐
│  │       Idle / Prepare       │  (internal use only)
│  └───────────┬───────────────┘
│  ┌───────────┴───────────────┐
│  │          Poll              │  (retrieve new I/O events)
│  └───────────┬───────────────┘
│  ┌───────────┴───────────────┐
│  │          Check             │  (setImmediate callbacks)
│  └───────────┬───────────────┘
│  ┌───────────┴───────────────┐
│  │      Close Callbacks       │  (e.g., socket.on('close'))
│  └───────────┬───────────────┘
└──────────────┘
```

**Sample answer:** *"The event loop is what lets Node handle thousands of concurrent operations on a single thread. When Node starts, it initializes the loop, processes the input script, then enters the loop. Each iteration (or 'tick') goes through phases — timers, pending callbacks, poll, check, and close. I/O operations are offloaded to the OS or thread pool, and their callbacks are queued for a future tick."*

---

### 3. What is the difference between `process.nextTick()` and `setImmediate()`?

Both schedule callbacks to run asynchronously, but at different points in the event loop:

- **`process.nextTick()`** — runs *before* the event loop continues to the next phase. It fires after the current operation completes, but before any I/O or timer callbacks.
- **`setImmediate()`** — runs in the **Check** phase of the event loop, *after* the Poll phase.

```js
setImmediate(() => console.log('setImmediate'));
process.nextTick(() => console.log('nextTick'));
console.log('synchronous');

// Output:
// synchronous
// nextTick
// setImmediate
```

**When to use which:**
- Use `process.nextTick()` when you need something to run immediately after the current operation (e.g., emitting an event after a constructor returns).
- Use `setImmediate()` when you want to yield to the event loop so I/O can proceed.

**Warning:** Recursive `process.nextTick()` calls can starve the event loop because they always run before I/O.

---

### 4. Explain non-blocking I/O in Node.js.

In traditional (blocking) I/O, a thread waits idle while a file read or network request completes. Node.js uses **non-blocking I/O** — when you make an I/O call, Node hands the work off to the OS (or libuv's thread pool) and immediately moves on to execute the next line of code. When the I/O completes, a callback is placed on the event queue.

```js
// Non-blocking: execution continues immediately
const fs = require('fs');

fs.readFile('/big-file.txt', (err, data) => {
  console.log('File read complete');  // runs later
});

console.log('This runs first');  // runs immediately
```

**Sample answer:** *"Non-blocking I/O means Node doesn't wait around for disk reads, network calls, or database queries to finish. It delegates those to the OS via libuv and registers a callback. The event loop picks up the result when it's ready. This is why a single Node process can handle thousands of concurrent connections — it's never sitting idle waiting for I/O."*

---

### 5. What are Streams in Node.js? What are the different types?

Streams are objects that let you read or write data **piece by piece** (in chunks) rather than loading everything into memory at once. They're essential for handling large files, network data, or any I/O where data flows over time.

**Four types of streams:**

1. **Readable** — source of data (e.g., `fs.createReadStream()`, `http.IncomingMessage`)
2. **Writable** — destination for data (e.g., `fs.createWriteStream()`, `http.ServerResponse`)
3. **Duplex** — both readable and writable (e.g., `net.Socket`)
4. **Transform** — a duplex stream that can modify data as it passes through (e.g., `zlib.createGzip()`)

```js
const fs = require('fs');
const zlib = require('zlib');

// Pipe a file through gzip compression and write to a new file
fs.createReadStream('input.txt')
  .pipe(zlib.createGzip())
  .pipe(fs.createWriteStream('input.txt.gz'));
```

**Why streams matter:** Reading a 2 GB file with `fs.readFile()` would consume 2 GB of memory. With `fs.createReadStream()`, you process it in small chunks (default 64 KB), keeping memory usage low.

---

### 6. What is the difference between `require()` and `import`?

These are two different module systems:

| | `require()` (CommonJS) | `import` (ES Modules) |
|---|---|---|
| **Loading** | Synchronous | Asynchronous |
| **When evaluated** | At runtime (dynamic) | At parse time (static) |
| **Syntax** | `const x = require('x')` | `import x from 'x'` |
| **Exports** | `module.exports = ...` | `export default ...` / `export const ...` |
| **Tree-shaking** | Not possible | Supported (dead code elimination) |
| **Conditional imports** | Yes (`if (cond) require(...)`) | Only via dynamic `import()` |
| **File extension** | `.js` (default) | `.mjs` or `"type": "module"` in package.json |

```js
// CommonJS
const express = require('express');
module.exports = { myFunc };

// ES Modules
import express from 'express';
export const myFunc = () => {};
```

**Sample answer:** *"CommonJS uses `require()` and loads modules synchronously at runtime — it's been the Node standard since the beginning. ES Modules use `import/export`, are loaded asynchronously, and allow static analysis for tree-shaking. Modern Node supports both, but you need to use `.mjs` extensions or set `"type": "module"` in package.json for ESM."*

---

### 7. What is the purpose of `package.json` and `package-lock.json`?

**`package.json`** is the manifest for your Node project. It contains:
- Project metadata (name, version, description)
- **Dependencies** — packages your app needs to run
- **devDependencies** — packages only needed during development
- **Scripts** — custom commands (`npm run build`, `npm test`, etc.)
- Engine requirements, entry points, and more

**`package-lock.json`** is an auto-generated file that locks down the **exact versions** of every installed package (including nested dependencies). It ensures that every developer and every CI/CD pipeline installs the identical dependency tree.

```json
// package.json — loose version ranges
"dependencies": {
  "express": "^4.18.0"   // could install 4.18.0, 4.18.2, 4.19.1, etc.
}

// package-lock.json — exact pinned versions
"express": {
  "version": "4.18.2",   // exactly this version
  "resolved": "https://registry.npmjs.org/express/-/express-4.18.2.tgz",
  "integrity": "sha512-..."
}
```

**Key rule:** Always commit `package-lock.json` to version control.

---

### 8. How does the Node.js module caching mechanism work?

When you `require()` a module for the first time, Node does the following:

1. **Resolves** the file path
2. **Loads** the file from disk
3. **Wraps** it in a function (the module wrapper)
4. **Executes** the code
5. **Caches** the resulting `module.exports` object

On subsequent `require()` calls for the same module, Node **returns the cached version** — it does not re-read the file or re-execute the code.

```js
// counter.js
let count = 0;
module.exports = { increment: () => ++count, getCount: () => count };

// app.js
const a = require('./counter');
const b = require('./counter');  // same cached instance!

a.increment();
console.log(b.getCount());  // 1  (a and b point to the same object)
```

You can inspect the cache via `require.cache` and even delete entries to force a re-load (though this is rarely advisable in production).

---

### 9. What is the difference between `dependencies` and `devDependencies`?

- **`dependencies`** — packages required for your application to run in production. Examples: `express`, `mongoose`, `dotenv`.
- **`devDependencies`** — packages only needed during development or testing. Examples: `jest`, `eslint`, `nodemon`, `typescript`.

```bash
npm install express          # saved to dependencies
npm install jest --save-dev  # saved to devDependencies
```

When you deploy to production and run `npm install --production` (or `NODE_ENV=production`), only `dependencies` are installed — `devDependencies` are skipped. This keeps production builds leaner and faster.

---

### 10. Explain Node.js single-threaded architecture. How does it handle concurrency?

Node.js runs your JavaScript on a **single main thread**. However, it achieves concurrency through:

1. **The Event Loop** — orchestrates asynchronous callbacks
2. **libuv's Thread Pool** — handles CPU-intensive or blocking operations (DNS lookups, file system operations, compression) on a pool of worker threads (default: 4, configurable via `UV_THREADPOOL_SIZE`)
3. **OS-level async I/O** — network I/O (TCP/UDP) is handled by the OS kernel using mechanisms like `epoll` (Linux), `kqueue` (macOS), or IOCP (Windows)

```
    ┌─────────────────┐
    │  Your JS Code    │   ← single-threaded
    │  (main thread)   │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │   Event Loop     │   ← dispatches callbacks
    └────────┬────────┘
             │
   ┌─────────┴─────────┐
   │                    │
┌──▼──┐          ┌─────▼─────┐
│ OS  │          │  Thread   │
│Async│          │   Pool    │
│ I/O │          │ (libuv)   │
└─────┘          └───────────┘
Network I/O       File I/O, DNS,
                  crypto, zlib
```

**Sample answer:** *"Node is single-threaded for JavaScript execution, but not for everything else. I/O operations are delegated either to the OS (for network I/O) or to libuv's thread pool (for file system, DNS, and crypto). The event loop ties it all together by picking up completed operations and running their callbacks on the main thread. This model is highly efficient for I/O-bound workloads."*

---

## Part 2: Intermediate (Questions 11–18)

### 11. What are callbacks, and what is "callback hell"? How do you avoid it?

A **callback** is a function passed as an argument to another function, to be executed once an async operation completes. Node follows the **error-first callback** convention: the first argument is always an error (or `null`).

```js
fs.readFile('file.txt', 'utf8', (err, data) => {
  if (err) return console.error(err);
  console.log(data);
});
```

**Callback hell** happens when you nest many async callbacks inside each other, creating deeply indented, hard-to-read code:

```js
getUser(id, (err, user) => {
  getOrders(user.id, (err, orders) => {
    getOrderDetails(orders[0].id, (err, details) => {
      getProduct(details.productId, (err, product) => {
        // ... deeply nested and hard to maintain
      });
    });
  });
});
```

**How to avoid it:**
1. **Promises** — chain `.then()` calls instead of nesting
2. **async/await** — write async code that reads like synchronous code
3. **Modularize** — break callbacks into named functions
4. **Libraries** — use control flow libraries like `async.js` (less common now)

---

### 12. Explain Promises and how they improve async flow control.

A **Promise** represents a value that may not be available yet but will be resolved (or rejected) at some point in the future. It has three states:

- **Pending** — initial state, neither fulfilled nor rejected
- **Fulfilled** — the operation completed successfully
- **Rejected** — the operation failed

```js
function readFileAsync(path) {
  return new Promise((resolve, reject) => {
    fs.readFile(path, 'utf8', (err, data) => {
      if (err) reject(err);
      else resolve(data);
    });
  });
}

// Chaining instead of nesting
readFileAsync('config.json')
  .then(data => JSON.parse(data))
  .then(config => connectToDb(config.dbUrl))
  .then(db => db.query('SELECT * FROM users'))
  .catch(err => console.error('Something failed:', err));
```

**Why Promises are better than raw callbacks:**
- Flat chaining instead of deep nesting
- Centralized error handling with `.catch()`
- Composable with `Promise.all()`, `Promise.race()`, etc.
- Foundation for `async/await`

Most modern Node APIs (since v10+) offer promise-based versions: `fs.promises.readFile()`, `dns.promises.lookup()`, etc.

---

### 13. What is `async/await`, and how does it relate to Promises?

`async/await` is syntactic sugar on top of Promises that lets you write asynchronous code in a synchronous style.

- **`async`** before a function makes it return a Promise
- **`await`** pauses execution inside that function until the Promise resolves

```js
// With Promises
function getUser(id) {
  return fetch(`/api/users/${id}`)
    .then(res => res.json())
    .then(user => fetch(`/api/orders/${user.orderId}`))
    .then(res => res.json());
}

// With async/await — same logic, much cleaner
async function getUser(id) {
  const userRes = await fetch(`/api/users/${id}`);
  const user = await userRes.json();
  const orderRes = await fetch(`/api/orders/${user.orderId}`);
  return orderRes.json();
}
```

**Error handling** uses standard `try/catch`:

```js
async function loadConfig() {
  try {
    const data = await fs.promises.readFile('config.json', 'utf8');
    return JSON.parse(data);
  } catch (err) {
    console.error('Failed to load config:', err.message);
    return defaultConfig;
  }
}
```

**Important:** `await` only pauses the *current* async function — it does not block the event loop or other operations.

---

### 14. What is the difference between `Promise.all()`, `Promise.allSettled()`, `Promise.race()`, and `Promise.any()`?

```js
const p1 = fetch('/api/users');
const p2 = fetch('/api/orders');
const p3 = fetch('/api/products');
```

| Method | Resolves when... | Rejects when... | Use case |
|---|---|---|---|
| `Promise.all([p1, p2, p3])` | **All** promises fulfill | **Any one** rejects | Parallel fetches where you need all results |
| `Promise.allSettled([p1, p2, p3])` | **All** promises settle (fulfill or reject) | Never rejects | Parallel operations where you want all results regardless of failures |
| `Promise.race([p1, p2, p3])` | **First** promise to settle (fulfill *or* reject) | First to settle is a rejection | Timeouts, fastest response wins |
| `Promise.any([p1, p2, p3])` | **First** promise to fulfill | **All** reject (`AggregateError`) | Try multiple sources, take the first success |

```js
// Promise.all — fail fast
const [users, orders] = await Promise.all([getUsers(), getOrders()]);

// Promise.allSettled — get everything, handle failures individually
const results = await Promise.allSettled([getUsers(), getOrders()]);
results.forEach(r => {
  if (r.status === 'fulfilled') console.log(r.value);
  else console.error(r.reason);
});

// Promise.race — timeout pattern
const result = await Promise.race([
  fetch('/api/data'),
  new Promise((_, reject) => setTimeout(() => reject('Timeout'), 5000))
]);
```

---

### 15. How do you handle errors in async code?

**Callbacks** — check the `err` argument first:
```js
fs.readFile('file.txt', (err, data) => {
  if (err) return handleError(err);  // always check err first
  processData(data);
});
```

**Promises** — use `.catch()` or a final catch block:
```js
fetchData()
  .then(process)
  .catch(err => console.error(err));  // catches errors from any step
```

**async/await** — use `try/catch`:
```js
try {
  const data = await fetchData();
  const result = await process(data);
} catch (err) {
  console.error('Operation failed:', err);
}
```

**Global safety nets** (don't rely on these as primary error handling):
```js
// Uncaught exceptions (synchronous)
process.on('uncaughtException', (err) => {
  console.error('Uncaught:', err);
  process.exit(1);  // process is in an undefined state — exit
});

// Unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection:', reason);
});
```

**Best practices:**
- Always handle errors at every async boundary
- Use `uncaughtException` only for logging/cleanup before crashing — never try to resume
- In Express, use error-handling middleware: `app.use((err, req, res, next) => { ... })`

---

### 16. What is the Cluster module, and how does it help with scaling?

Node runs on a single thread, meaning it can only use **one CPU core** by default. The `cluster` module lets you fork multiple worker processes that share the same server port, utilizing all available cores.

```js
const cluster = require('cluster');
const http = require('http');
const os = require('os');

if (cluster.isPrimary) {
  const numCPUs = os.cpus().length;
  console.log(`Primary ${process.pid} forking ${numCPUs} workers`);

  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }

  cluster.on('exit', (worker) => {
    console.log(`Worker ${worker.process.pid} died. Restarting...`);
    cluster.fork();  // auto-restart on crash
  });

} else {
  http.createServer((req, res) => {
    res.end(`Handled by worker ${process.pid}\n`);
  }).listen(3000);
}
```

**How it works:** The primary process doesn't handle requests — it forks worker processes (using `child_process.fork()`). The OS distributes incoming connections across workers (round-robin on most platforms).

In production, most people use **PM2** instead of manually writing cluster code: `pm2 start app.js -i max`.

---

### 17. What are Worker Threads, and when would you use them over the Cluster module?

**Worker Threads** (`worker_threads` module) run JavaScript in parallel threads within a single process, sharing memory via `SharedArrayBuffer`.

| | Cluster | Worker Threads |
|---|---|---|
| **Creates** | Separate processes | Threads in same process |
| **Memory** | Each process has its own memory | Can share memory (`SharedArrayBuffer`) |
| **Communication** | IPC (inter-process communication) | `postMessage` + shared memory |
| **Use case** | Scaling HTTP servers across CPU cores | CPU-intensive computation |
| **Overhead** | Higher (full process per worker) | Lower (threads are lighter) |

```js
const { Worker, isMainThread, parentPort } = require('worker_threads');

if (isMainThread) {
  const worker = new Worker(__filename);
  worker.on('message', (result) => {
    console.log('Fibonacci result:', result);
  });
  worker.postMessage(45);  // compute fib(45) in background
} else {
  parentPort.on('message', (n) => {
    function fib(n) { return n <= 1 ? n : fib(n - 1) + fib(n - 2); }
    parentPort.postMessage(fib(n));
  });
}
```

**When to use what:**
- **Cluster** → you want to scale an HTTP server across multiple cores
- **Worker Threads** → you have CPU-heavy tasks (image processing, encryption, data parsing) and want to offload them without blocking the main thread

---

### 18. How would you identify and fix a memory leak in a Node.js application?

**Symptoms:** Increasing RSS (Resident Set Size), slow responses over time, eventual crashes with "JavaScript heap out of memory."

**Step 1 — Monitor memory:**
```js
setInterval(() => {
  const mem = process.memoryUsage();
  console.log(`Heap: ${(mem.heapUsed / 1024 / 1024).toFixed(1)} MB`);
}, 10000);
```

**Step 2 — Take heap snapshots:**
```js
// Using --inspect flag
// node --inspect app.js
// Open chrome://inspect → Take Heap Snapshot → Compare snapshots
```

Or programmatically with `v8.writeHeapSnapshot()`.

**Step 3 — Common causes and fixes:**

| Cause | Example | Fix |
|---|---|---|
| Unbounded caches | `const cache = {}; cache[key] = data;` | Use `Map` with TTL or LRU cache (`lru-cache` package) |
| Event listener leaks | Adding listeners in a loop without removing | Call `removeListener()` or `off()` when done |
| Global variables | Accidental globals (`x = 5` without `let/const`) | Always use `let`/`const`; use `'use strict'` |
| Closures holding references | Callbacks referencing large objects | Nullify references when done |
| Unclosed resources | DB connections, file handles | Always close/release in `finally` blocks |

**Tools:** Node's built-in `--inspect` with Chrome DevTools, `clinic.js`, `heapdump`, `memwatch-next`.

---

## Part 3: Advanced (Questions 19–25)

### 19. What is the V8 Garbage Collector, and how does it affect performance?

V8 (the JS engine inside Node) uses a **generational garbage collector** with two main areas:

- **Young Generation (Scavenger)** — small, fast. New objects are allocated here. Collected frequently using a "semi-space" algorithm (copy live objects from one half to the other).
- **Old Generation (Mark-Sweep-Compact)** — larger, slower. Objects that survive multiple young-generation collections are "promoted" here. Collected less frequently.

**How GC affects performance:**
- **Minor GC** (young gen) — fast (1–2 ms), but happens often
- **Major GC** (old gen) — can cause noticeable pauses (10–100+ ms)

**Tips to reduce GC pressure:**
- Avoid creating many short-lived objects in hot loops
- Reuse objects/buffers instead of creating new ones
- Use `--max-old-space-size` to increase heap for memory-intensive apps
- Stream data instead of buffering entire payloads
- Profile with `--trace-gc` to see GC activity

```bash
node --trace-gc app.js
# Output: Scavenge 3.2 (6.0) -> 2.1 (7.0) MB, 1.3 ms
# Output: Mark-sweep 45.1 (70.0) -> 30.2 (70.0) MB, 23.5 ms
```

---

### 20. What is the purpose of the `Buffer` class?

`Buffer` is a Node.js class for handling **raw binary data** directly in memory, outside the V8 heap. It exists because JavaScript strings are UTF-16 encoded, which isn't ideal for working with binary protocols, file I/O, or network streams.

```js
// Creating buffers
const buf1 = Buffer.from('Hello', 'utf8');    // from a string
const buf2 = Buffer.alloc(10);                 // 10 zero-filled bytes
const buf3 = Buffer.from([0x48, 0x69]);        // from byte array

// Common operations
console.log(buf1.toString('utf8'));    // 'Hello'
console.log(buf1.toString('base64')); // 'SGVsbG8='
console.log(buf1.length);             // 5 (bytes, not characters)
console.log(buf1[0]);                 // 72 (ASCII for 'H')

// Concatenation
const combined = Buffer.concat([buf1, buf3]);
```

**When you encounter Buffers:** reading files without specifying encoding, receiving data from TCP sockets, working with crypto operations, handling image/audio data.

**Security note:** Always use `Buffer.alloc()` (zero-filled) instead of `Buffer.allocUnsafe()` unless you're certain you'll overwrite every byte — unsafe buffers may contain old memory data.

---

### 21. How does middleware work in Express.js?

Middleware functions are functions that have access to the **request** (`req`), **response** (`res`), and a **`next`** function. They execute in order and form a pipeline — each can modify the request/response, end the response, or pass control to the next middleware.

```js
const express = require('express');
const app = express();

// Middleware 1: Logging (runs for every request)
app.use((req, res, next) => {
  console.log(`${req.method} ${req.url}`);
  next();  // pass control to next middleware
});

// Middleware 2: Authentication (runs for every request)
app.use((req, res, next) => {
  const token = req.headers.authorization;
  if (!token) return res.status(401).json({ error: 'No token' });
  req.user = verifyToken(token);
  next();
});

// Route handler (also middleware, but typically the end of the chain)
app.get('/api/profile', (req, res) => {
  res.json({ user: req.user });
});

// Error-handling middleware (4 arguments — must have all four)
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong' });
});
```

**Execution order matters.** Middleware is called in the order you define it. A common mistake is placing error handlers before routes, or placing `express.json()` after route handlers that need parsed bodies.

**Types:** application-level (`app.use`), router-level (`router.use`), built-in (`express.json()`, `express.static()`), third-party (`cors`, `helmet`), error-handling (4 params).

---

### 22. What is the difference between `spawn`, `exec`, `execFile`, and `fork`?

All are from the `child_process` module and create child processes, but they differ in behavior:

| Method | Returns | Shell? | Data | Best for |
|---|---|---|---|---|
| `spawn` | `ChildProcess` (stream) | No | Streamed | Long-running processes, large output |
| `exec` | `ChildProcess` (buffered) | Yes | Buffered (max ~1 MB) | Short commands, need shell features |
| `execFile` | `ChildProcess` (buffered) | No | Buffered | Running a specific binary (safer than exec) |
| `fork` | `ChildProcess` (with IPC) | No | IPC channel | Running Node.js scripts with message passing |

```js
const { spawn, exec, execFile, fork } = require('child_process');

// spawn — streams output as it comes
const ls = spawn('ls', ['-la', '/tmp']);
ls.stdout.on('data', (data) => console.log(data.toString()));

// exec — buffers output, supports shell syntax (pipes, redirects)
exec('cat /etc/passwd | grep root', (err, stdout) => {
  console.log(stdout);
});

// execFile — like exec but safer (no shell injection risk)
execFile('/usr/bin/git', ['status'], (err, stdout) => {
  console.log(stdout);
});

// fork — creates a new Node.js process with IPC
const child = fork('./worker.js');
child.send({ task: 'processData' });
child.on('message', (result) => console.log(result));
```

**Security tip:** Prefer `spawn` or `execFile` over `exec` when possible — `exec` uses a shell, which makes it vulnerable to shell injection if user input is not properly sanitized.

---

### 23. How do you secure a Node.js application?

**Input & Injection:**
- Validate and sanitize all user input (use `joi`, `zod`, or `express-validator`)
- Use parameterized queries for databases (never concatenate SQL strings)
- Sanitize HTML to prevent XSS (`DOMPurify`, `sanitize-html`)

**Dependencies:**
- Run `npm audit` regularly to catch known vulnerabilities
- Keep dependencies up to date
- Lock dependency versions with `package-lock.json`

**HTTP Security:**
- Use `helmet` middleware (sets security headers like `Content-Security-Policy`, `X-Frame-Options`)
- Enable CORS properly (don't use `*` in production)
- Use HTTPS everywhere

**Authentication & Authorization:**
- Hash passwords with `bcrypt` (never store plain text)
- Use JWTs with short expiration times and secure storage
- Implement rate limiting (`express-rate-limit`) to prevent brute force

**General:**
- Never expose stack traces or error details in production
- Set `NODE_ENV=production` to disable verbose errors
- Don't run the Node process as root
- Use environment variables for secrets (never hardcode them)

---

### 24. What are EventEmitters, and how do you create custom ones?

An `EventEmitter` is a class that allows objects to emit named events and register listeners for those events. It's the foundation of Node's event-driven architecture — streams, HTTP servers, and many core modules extend it.

```js
const EventEmitter = require('events');

// Custom class extending EventEmitter
class OrderProcessor extends EventEmitter {
  process(order) {
    this.emit('processing', order.id);

    // simulate async work
    setTimeout(() => {
      if (order.total > 0) {
        this.emit('complete', order);
      } else {
        this.emit('error', new Error(`Invalid order: ${order.id}`));
      }
    }, 1000);
  }
}

// Usage
const processor = new OrderProcessor();

processor.on('processing', (id) => console.log(`Processing order ${id}...`));
processor.on('complete', (order) => console.log(`Order ${order.id} complete!`));
processor.on('error', (err) => console.error(err.message));

processor.process({ id: 'ORD-123', total: 49.99 });
```

**Key methods:**
- `.on(event, listener)` — add a listener
- `.once(event, listener)` — listener fires only once
- `.emit(event, ...args)` — trigger an event
- `.removeListener(event, listener)` — remove a specific listener
- `.removeAllListeners(event)` — remove all listeners for an event

**Gotcha:** By default, Node warns if more than 10 listeners are added for a single event (possible memory leak). Increase with `emitter.setMaxListeners(n)` if needed.

---

### 25. Explain the difference between `readFile` and `createReadStream` — when would you choose one over the other?

| | `fs.readFile()` | `fs.createReadStream()` |
|---|---|---|
| **How it works** | Reads the **entire** file into memory as a Buffer | Reads the file in **chunks** (default 64 KB) |
| **Memory** | Uses memory equal to file size | Uses only the chunk size at a time |
| **When data is available** | After the entire file is read | As soon as the first chunk is ready |
| **Returns** | Buffer or string (via callback/promise) | Readable Stream |

```js
// readFile — fine for small files (config, JSON, small templates)
const data = await fs.promises.readFile('config.json', 'utf8');
const config = JSON.parse(data);

// createReadStream — essential for large files
const stream = fs.createReadStream('huge-video.mp4');
stream.pipe(res);  // pipe directly to HTTP response
```

**When to use `readFile`:**
- Small files (config files, templates, JSON under a few MB)
- When you need the complete content before doing anything

**When to use `createReadStream`:**
- Large files (videos, logs, datasets)
- When serving files over HTTP (pipe the stream directly to the response)
- When processing data line by line or chunk by chunk
- When memory efficiency matters

**Rule of thumb:** If the file could be larger than ~50 MB, always use a stream.

---

## Quick-Reference Cheat Sheet

| Topic | One-liner |
|---|---|
| Event Loop | Single-threaded scheduler that dispatches async callbacks across phases |
| Non-blocking I/O | Node delegates I/O to the OS/thread pool and continues executing |
| Streams | Process data in chunks to avoid loading everything into memory |
| Cluster | Fork multiple processes to use all CPU cores |
| Worker Threads | Run CPU-intensive JS in parallel threads within one process |
| Buffers | Handle raw binary data outside the V8 string system |
| EventEmitter | Pub/sub pattern: emit events, register listeners |
| Middleware | Pipeline of functions that process requests in order |

---

*Good luck with your interview preparation, Vikash!*
