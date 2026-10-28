# JavaScript package

Status: specification for `small-python` on npm.

## 1 Goals

1. Run untrusted Python code, including code written by a language model,
   from JavaScript. Nothing the engine does, including a memory-safety bug
   triggered on purpose, may crash, hang, or take over the JavaScript program.
2. Give engine code exactly the host functions and modules the embedder
   grants, and nothing else.
3. Mirror the Python package (`python.md`) wherever JavaScript allows, and
   speak the same worker protocol (`protocol.md`).
4. Run unchanged in Node.js and in browsers, with no dependencies and no
   native addon.

Not goals: synchronous evaluation, sharing JavaScript objects with engine
code, file access.

## 2 Architecture

The engine and `spy-worker.c` compile to one WebAssembly module,
`spy-worker.wasm`, built for `wasm32-wasip1` with wasi-sdk. Each `Runtime`
starts a dedicated Worker thread that instantiates the module and runs the
worker's `main`, which loops reading requests. Two kinds of separation stack:

1. **WebAssembly.** Engine code, and anything that corrupts the engine's
   memory, can touch only the module's linear memory and call only its
   imports. The imports are the two stream functions below and a WASI shim
   that writes diagnostics, reads clocks, exits, and refuses everything else
   (`ENOSYS`; no preopened directories). A trap (an `abort`,
   an out-of-bounds access) ends the Worker, not the program.
2. **A Worker thread.** The engine blocks while it runs; the Worker keeps the
   main thread responsive and can be terminated at any time, which is how
   `timeout` works.

```text
main thread                                   Worker thread
+----------------------------+  postMessage  +------------------------+
| Runtime, PyObject proxies, | <------------ | spy-worker.wasm        |
| host functions, loader,    |               |   SPYContext, handles  |
| output                     | ------------> |   blocks in read()     |
+----------------------------+  shared buffer +------------------------+
```

### 2.1 Streams

Worker to main: the module's `write(pointer, length)` import copies the bytes
and posts them. Posted messages keep their order; the main thread reassembles
frames from them.

Main to worker: the Worker is blocked inside the engine, so it cannot receive
posted messages. Instead each runtime owns a `SharedArrayBuffer` *inbox*: two
`Int32` cells, `state` and `length`, then a data area of 64 KiB. The module's
`read(pointer, capacity)` import:

1. waits with `Atomics.wait` while `state` is 0;
2. copies up to `capacity` bytes from the data area, keeping its position;
3. when the chunk is used up, stores 0 in `state` and calls `Atomics.notify`.

The main thread writes a message as successive chunks: for each, it waits
with `Atomics.waitAsync` until `state` is 0, copies the chunk, stores
`length`, stores 1 in `state`, and calls `Atomics.notify`. Only one message
is written at a time (`protocol.md` §6 gives the turn to one side).

### 2.2 Memory

The module imports its memory, 16 MiB initially (stack, static data, and
protocol buffers). The Runtime gives it a maximum of those 16 MiB plus 1.25 ×
`memoryLimit`, for the allocator's own overhead (or the 4 GiB `wasm32`
maximum when unlimited), so even an allocator bug cannot grow the Worker
beyond it. The engine's C stack is 8 MiB, matching the engine's own
4 MiB recursion guard with room to spare.

## 3 API

```js
import { Runtime, PyObject, Complex, keywords,
         PythonError, WorkerError, Timeout } from "small-python";
```

All methods that reach the engine return promises.

### 3.1 `Runtime`

```js
const rt = await Runtime.create({
  std: true, stepLimit: 0, memoryLimit: 0, timeout: undefined,
  output: undefined, loader: undefined, messageLimit: 64 * 2 ** 20,
});
```

| Option | Meaning |
|---|---|
| `std` | Register the standard modules. |
| `stepLimit` | Evaluation steps per top-level `eval` or `exec`; `0` is unlimited. Exceeding it raises `RuntimeError` in the engine. |
| `memoryLimit` | Bytes the engine may hold; `0` is unlimited. Exceeding it raises `MemoryError` in the engine. |
| `timeout` | Milliseconds a single operation may run in the worker, or `undefined`. Exceeding it terminates the Worker and rejects with `Timeout`. |
| `output` | `(text) => void \| Promise<void>` receiving printed text; by default each complete line goes to `console.log`, and an unfinished line when the operation ends. |
| `loader` | `(name) => string \| null \| Promise<string \| null>` mapping module names to source. |
| `messageLimit` | Largest message in bytes, either direction. |

`Runtime.create` rejects with `WorkerError` when the Worker cannot start,
including when `SharedArrayBuffer` is unavailable (§5).

Methods:

| Method | Python package equivalent |
|---|---|
| `eval(source, filename = "<string>")` | `rt.eval` |
| `exec(source, filename = "<string>")` | `rt.exec` |
| `call(target, args = [], kwargs = {})` | `rt.call(target, *args, **kwargs)` |
| `get(name)`, `set(name, value)`, `delete(name)` | `rt[name]`, `rt[name] = value`, `del rt[name]` |
| `define(name, fn)` | `rt.define` |
| `registerModule(name, members = null, source = null)` | `rt.register_module`; `members` is a plain object or `Map` |
| `collect()` | `rt.collect` |
| `close()` | `rt.close`; synchronous: terminates the Worker |
| `closed` | `rt.closed` |
| `version` | the engine version, from the `INIT` reply |

`get` of a missing name rejects with `PythonError` of type `NameError`, and
`delete` of one with type `KeyError`. `define` names the engine function after
the global, so anonymous functions get a useful `__name__`. A `Runtime` also
implements `Symbol.dispose` for `using`.

### 3.2 Conversion

JavaScript to engine:

| JavaScript | Engine |
|---|---|
| `null`, `undefined` | `None` |
| boolean | `bool` |
| number that is an integer, other than `-0` | `int` |
| other number (fractions, `-0`, `NaN`, infinities) | `float` |
| bigint | `int` |
| string | `str`; a surrogate pair is one code point, a lone surrogate is kept |
| `Uint8Array` | `bytes` |
| `Array` | `list` |
| `Set` | `set` |
| `Map`, or an object whose prototype is `Object.prototype` or `null` | `dict` (object keys are strings) |
| `Complex` | `complex` |
| function | native function |
| `PyObject` | the engine value; from another runtime: `TypeError` |
| anything else | `TypeError` |

Engine to JavaScript:

| Engine (exact type) | JavaScript |
|---|---|
| `None` | `null` |
| `bool` | boolean |
| `int` | number when it is a safe integer, else bigint |
| `float` | number |
| `complex` | `Complex` (frozen; `real`, `imag`) |
| `str` | string |
| `bytes`, `bytearray` | `Uint8Array` (a copy) |
| `list`, `tuple` | `Array` |
| `set`, `frozenset` | `Set` |
| `dict` | `Map` |
| anything else | `PyObject` |

JavaScript values nested deeper than 200 levels reject with `TypeError`;
engine values that deep reject with `PythonError` of type `RecursionError`
(`protocol.md` §4).

### 3.3 Host functions

A function is called with the positional arguments spread. Keyword arguments
raise `TypeError` in the engine unless the function is wrapped with
`keywords(fn)`; then it is called as `fn(...args, kwargs)` with `kwargs` a
null-prototype object, empty when there are none. A host function may be
`async`; the engine waits for its promise. While it runs it may call `call`,
`get`, `set`, `define`, and `PyObject` methods of the same runtime (nested
requests, `protocol.md` §6), but not `eval` or `exec`, which reject.

A thrown value becomes an engine exception (`protocol.md` §7.4): a
`PythonError` from the same runtime re-raises its engine exception; an
`Error` maps its `name` and its prototype chain's names onto the engine's
builtin classes (`TypeError`, `RangeError` ... fall back to `RuntimeError`)
with its `message`; any other thrown value becomes `RuntimeError` with
`String(value)`. When engine code does not handle it, the `PythonError` that
rejects the operation has the original as its `cause`.

The loader follows the same rules and sees the same probe names as in Python
(`python.md` §3.5). An exception from `output` is reported with
`console.error`, and the engine's `print` raises `OSError`.

### 3.4 `PyObject`

A proxy for an engine value held by the worker.

| Method | Engine operation |
|---|---|
| `get(name)`, `set(name, value)` | attribute get and set |
| `getItem(key)`, `setItem(key, value)` | item get and set |
| `len()`, `has(item)` | `len`, `in` |
| `call(args = [], kwargs = {})` | call |
| `bool()`, `hash()` | truth value, `hash` |
| `compare(op, other)` | `op` one of `<`, `<=`, `==`, `!=`, `>`, `>=` |
| `repr()`, `str()`, `dir()` | `repr`, `str`, `dir` |
| `[Symbol.asyncIterator]()` | iteration: `for await (const x of obj)` |
| `release()` | drop the handle now |

Every method returns a promise; failures reject with `PythonError`. A
`FinalizationRegistry` releases the handles of collected proxies with the
next message; `release()` does it explicitly. After release, close, or loss,
methods reject.

### 3.5 Errors

`PythonError extends Error`: `type`, `message`, `exception` (`PyObject` or
`null`), `filename`, `lineno`; `name` is `"PythonError"`.

`WorkerError extends Error`: the worker was lost (`protocol.md` §8). `Timeout
extends WorkerError`: the timeout expired.

### 3.6 Concurrency

A runtime runs one operation at a time. An operation started while another is
running waits for it, in order, except that while a host function, the loader,
or output runs, operations of that runtime run immediately as nested requests
(`eval` and `exec` reject). Separate runtimes run in parallel.

## 4 Security

1. The WebAssembly module is the isolation boundary; the Worker gives it
   termination. Neither depends on the engine being correct.
2. The main thread validates every message as in `protocol.md` §2, bounds
   reads by `messageLimit`, and terminates the Worker on a violation.
3. The WASI shim gives the module no files, no network, no environment, and no
   arguments. `open()` raises `PermissionError`; the engine has no mounts.
4. Host functions are the security boundary the embedder writes.

## 5 Platforms

| Platform | Worker | Requirement |
|---|---|---|
| Node.js 20 and later | `worker_threads` | none |
| Browsers | module `Worker` | `crossOriginIsolated` (COOP and COEP headers), for `SharedArrayBuffer` |

Other runtimes with `Worker`, `SharedArrayBuffer`, `Atomics.waitAsync`, and
`WebAssembly` should work but are not tested.

The Worker is started with an empty `execArgv`, so flags of the embedding
process (`--inspect`, `--input-type`) do not reach it.

## 6 Package

```text
small-python/
  package.json        "type": "module", "exports": "./index.js"
  index.js            Runtime, PyObject, conversions, errors
  wire.js             value codec and framing (protocol.md §3–§4)
  worker.js           the Worker: WASI shim, streams, instantiation; it
                      moves bytes and decodes none
  spy-worker.wasm     the engine and worker
  index.d.ts          types
```

The repository builds `spy-worker.wasm` with `make wasm WASI_SDK=<path>`
(wasi-sdk 34 or later) and tests the package with `make test-javascript`.

## 7 Tests

As `python.md` §7, adapted: a Worker that exits or is terminated rejects with
`WorkerError`; a fake Worker sending malformed messages, or nothing at all;
`timeout` with an infinite loop and its exclusion of host time;
`memoryLimit`; nested and parallel async callbacks; handle release; queued
concurrent operations; and messages larger than the inbox, in both
directions. The suite runs on every supported Node.js major version.
