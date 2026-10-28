# small-python

Run [Small Python](https://github.com/soasme/small-python), a small Python 3.15
engine written in C, from JavaScript. The engine is compiled to WebAssembly
and each runtime runs in a Worker thread of its own: code in it sees only the
functions and modules you give it, cannot touch files, the network, or your
objects, and can be stopped at any time.

```sh
npm install small-python
```

```js
import { Runtime } from "small-python";

const rt = await Runtime.create({ memoryLimit: 64 << 20, timeout: 5000 });
await rt.define("fetchUser", async (id) => ({ id, name: "Ada" }));
console.log(await rt.eval("fetchUser(7)['name'].upper()"));  // ADA
rt.close();
```

## Values

Plain data is copied in both directions: `null`, booleans, numbers, bigints,
strings, `Uint8Array`, arrays, `Set`, `Map`, and plain objects. A Python
`dict` comes back as a `Map`, an `int` beyond 2⁵³ as a bigint. Functions you
pass in become Python functions; Python functions, instances, and other values
come back as `PyObject` proxies whose methods (`get`, `call`, `getItem`, ...)
return promises.

Host functions are called with positional arguments. Wrap one with
`keywords(fn)` to receive Python keyword arguments as a final object. They may
be `async`; the engine waits.

## Limits and safety

| Option | Effect |
|---|---|
| `stepLimit` | `RuntimeError` in Python after that many steps per `eval`/`exec` |
| `memoryLimit` | `MemoryError` in Python beyond that many bytes |
| `timeout` | terminates the worker after that many milliseconds; rejects with `Timeout` |
| `messageLimit` | largest value that may cross between JavaScript and Python |

A crash or a trap in the engine ends only its Worker: the operation rejects
with `WorkerError` and the runtime is closed.

## Platforms

Node.js 20 or later. In browsers the page must be cross-origin isolated
(COOP and COEP headers), because the worker uses `SharedArrayBuffer`.

The full specification is
[docs/packaging/javascript.md](https://github.com/soasme/small-python/blob/main/docs/packaging/javascript.md).
