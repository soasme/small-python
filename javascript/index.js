// Run Small Python from JavaScript. Each Runtime runs the engine, compiled to
// WebAssembly, in a Worker thread of its own and speaks the worker protocol
// to it (docs/packaging/protocol.md, docs/packaging/javascript.md).

import * as wire from "./wire.js";
import { Complex, Tuple, Violation } from "./wire.js";

export { Complex };

const node = typeof process === "object" && process.versions?.node;
const NodeWorker = node ? (await import("node:worker_threads")).Worker : null;

const INITIAL_PAGES = 256; // spy-worker.wasm is linked with 16 MiB of initial memory
const MAX_PAGES = 65536;
const INBOX = 64 * 1024;
const GRACE = 1000; // milliseconds past the timeout the worker has to stop the operation itself

let compiled;
function compile() {
  compiled ??= (async () => {
    const url = new URL("./spy-worker.wasm", import.meta.url);
    const bytes = node ? await (await import("node:fs/promises")).readFile(url) : await (await fetch(url)).arrayBuffer();
    return WebAssembly.compile(bytes);
  })();
  return compiled;
}

/** An engine exception that escaped. */
export class PythonError extends Error {
  constructor(type, message, exception = null, filename = null, lineno = null, options) {
    super(message, options);
    this.name = "PythonError";
    this.type = type;
    this.exception = exception;
    this.filename = filename;
    this.lineno = lineno;
  }
  toString() { return this.message ? `${this.type}: ${this.message}` : String(this.type); }
}

/** The worker was lost: it crashed, broke the protocol, or was terminated. */
export class WorkerError extends Error {
  constructor(message, returncode = null) {
    super(message);
    this.name = "WorkerError";
    this.returncode = returncode;
  }
}

/**
 * An operation ran past the runtime's timeout. The engine stops it and the
 * runtime stays open; a worker that does not stop within a grace period is
 * terminated, which closes the runtime.
 */
export class Timeout extends WorkerError {
  constructor(message) {
    super(message);
    this.name = "Timeout";
  }
}

const KEYWORDS = Symbol("small-python keywords");

/** Mark a host function as taking keyword arguments: fn(...args, kwargs). */
export function keywords(fn) {
  if (typeof fn !== "function") throw new TypeError("keywords() needs a function");
  const wrapped = function (...args) { return fn.apply(this, args); };
  Object.defineProperty(wrapped, "name", { value: fn.name });
  wrapped[KEYWORDS] = true;
  return wrapped;
}

const CREATE = Symbol("create");
const released = new FinalizationRegistry(({ runtime, id }) => runtime._release(id));

export class Runtime {
  /**
   * Start a runtime and its Worker.
   * @param {object} [options]
   */
  static async create(options = {}) {
    const runtime = new Runtime(CREATE, options);
    await runtime._start(options.std ?? true);
    return runtime;
  }

  constructor(token, options) {
    if (token !== CREATE) throw new TypeError("use Runtime.create()");
    const { stepLimit = 0, memoryLimit = 0, timeout, output, loader, messageLimit = 64 * 2 ** 20 } = options;
    for (const [name, limit] of [["stepLimit", stepLimit], ["memoryLimit", memoryLimit]])
      if (!Number.isSafeInteger(limit) || limit < 0) throw new RangeError(`${name} must be an integer >= 0`);
    if (!Number.isSafeInteger(messageLimit) || messageLimit < 1 || messageLimit > 0xffffffff)
      throw new RangeError("messageLimit must be an integer from 1 to 2**32 - 1");
    if (timeout !== undefined && !(timeout > 0)) throw new RangeError("timeout must be positive or undefined");
    if ((output !== undefined && typeof output !== "function") || (loader !== undefined && typeof loader !== "function"))
      throw new TypeError("output and loader must be functions or undefined");
    this._stepLimit = stepLimit;
    this._memoryLimit = memoryLimit;
    this._timeout = timeout;
    this._output = output;
    this._loader = loader;
    this._messageLimit = messageLimit;
    this._functions = new Map(); // function id -> { fn, keywords }
    this._functionIds = new Map(); // fn -> function id
    this._released = []; // handle ids to send with the next message
    this._failure = null; // { token, error } last raised into the engine
    this._tokens = 0;
    this._levels = [{ tail: Promise.resolve() }]; // one queue per callback depth
    this._timer = null;
    this._remaining = undefined;
    this._line = "";
    this._incoming = []; // chunks not yet framed
    this._incomingLength = 0;
    this._frames = [];
    this._waiter = null;
    this._lost = null;
    this._closed = false;
    this._lostSignal = new Promise((resolve) => { this._signalLost = resolve; });
    this.version = null;
  }

  async _start(std) {
    if (typeof SharedArrayBuffer !== "function")
      throw new WorkerError("SharedArrayBuffer is unavailable; a browser page must be cross-origin isolated");
    const module = await compile();
    this._inbox = new SharedArrayBuffer(8 + INBOX);
    this._control = new Int32Array(this._inbox, 0, 2);
    this._data = new Uint8Array(this._inbox, 8);
    const url = Runtime._workerURL;
    try {
      this._worker = node ? new NodeWorker(url, { execArgv: [] }) : new Worker(url, { type: "module" });
    } catch (e) {
      throw new WorkerError(`cannot start the worker: ${e.message}`);
    }
    const onMessage = (data) => {
      if (data instanceof Uint8Array) this._feed(data);
      else if ("exit" in data) this._lose(new WorkerError(`the worker exited with status ${data.exit}`, data.exit));
      else this._lose(new WorkerError(`the worker trapped: ${data.trap}`));
    };
    const onError = (e) => this._lose(new WorkerError(`the worker failed: ${e?.message ?? e}`));
    if (node) {
      this._worker.on("message", onMessage);
      this._worker.on("error", onError);
      this._worker.on("exit", (code) => this._lose(new WorkerError(`the worker exited with status ${code}`, code)));
    } else {
      this._worker.addEventListener("message", (event) => onMessage(event.data));
      this._worker.addEventListener("error", onError);
    }
    const limit = this._memoryLimit ? INITIAL_PAGES + Math.ceil(this._memoryLimit * 1.25 / 65536) : MAX_PAGES;
    this._worker.postMessage({ module, pages: INITIAL_PAGES, maximum: Math.min(limit, MAX_PAGES), inbox: this._inbox });
    this.version = await this._run(wire.INIT, [{
      std: Boolean(std), step_limit: this._stepLimit, memory_limit: this._memoryLimit,
      timeout: (this._timeout ?? 0) / 1000, message_limit: this._messageLimit,
    }]);
  }

  // Scheduling: one operation at a time per level; a host callback opens a
  // new level for the operations it makes.

  _run(kind, fields) {
    const level = this._levels.at(-1);
    const result = level.tail.then(() => this._operate(kind, fields, level));
    level.tail = result.catch(() => {});
    return result;
  }

  async _operate(kind, fields, level) {
    if (this._lost) throw this._copyLost();
    if (this._closed) throw new Error("the runtime is closed");
    if (level !== this._levels.at(-1)) throw new Error("the runtime is serving a host function");
    const top = this._levels.length === 1;
    if (top) {
      if (node) this._worker.ref();
      if (this._timeout !== undefined) this._startTimer(this._timeout + GRACE);
    }
    try {
      return await this._request(kind, fields);
    } finally {
      if (top) {
        this._stopTimer();
        this._flushLine();
        if (node && !this._lost && !this._closed) this._worker.unref();
      }
    }
  }

  async _request(kind, fields) {
    const data = wire.message(kind, fields, (value) => this._reference(value));
    if (data.length - 4 > this._messageLimit) throw new RangeError("message exceeds the limit");
    let reader = null;
    try {
      await this._send(data);
      reader = await this._awaitReply();
    } finally {
      if (!reader) this._lose(new WorkerError("the worker was terminated while it was running"));
    }
    const value = this._decode(reader, 1)[0];
    if (reader.kind === wire.RAISE) {
      this._checkError(value);
      throw this._engineError(value);
    }
    return value;
  }

  async _awaitReply() {
    for (;;) {
      const reader = await this._next();
      if (reader.kind === wire.RESULT || reader.kind === wire.RAISE) return reader;
      if (reader.kind !== wire.HOST && reader.kind !== wire.LOAD && reader.kind !== wire.OUTPUT)
        throw this._violation(`unexpected message kind 0x${reader.kind.toString(16)}`);
      await this._serve(reader);
    }
  }

  // The streams.

  async _send(data) {
    if (this._released.length) {
      const ids = this._released.splice(0);
      await this._write(wire.message(wire.RELEASE, [new Tuple(ids)], (value) => this._reference(value)));
    }
    await this._write(data);
  }

  async _write(data) {
    for (let at = 0; at < data.length;) {
      while (Atomics.load(this._control, 0) !== 0) {
        const wait = Atomics.waitAsync(this._control, 0, 1);
        if (wait.async) await Promise.race([wait.value, this._lostSignal]);
        if (this._lost) throw this._lost;
      }
      const n = Math.min(INBOX, data.length - at);
      this._data.set(data.subarray(at, at + n));
      this._control[1] = n;
      Atomics.store(this._control, 0, 1);
      Atomics.notify(this._control, 0);
      at += n;
    }
  }

  _feed(chunk) {
    if (this._lost) return;
    this._incoming.push(chunk);
    this._incomingLength += chunk.length;
    while (this._incomingLength >= 4) {
      const head = this._take(4, false);
      const n = new DataView(head.buffer, head.byteOffset, 4).getUint32(0, true);
      if (n < 1 || n > this._messageLimit) {
        this._lose(this._violationError("message length out of range"));
        return;
      }
      if (this._incomingLength < 4 + n) return;
      this._take(4, true);
      this._frames.push(new wire.Reader(this._take(n, true), (id) => this._obtain(id)));
    }
    if (this._waiter && this._frames.length) {
      const { resolve } = this._waiter;
      this._waiter = null;
      resolve(this._frames.shift());
    }
  }

  _take(n, consume) {
    const out = new Uint8Array(n);
    let filled = 0, index = 0;
    while (filled < n) {
      const chunk = this._incoming[index];
      const k = Math.min(n - filled, chunk.length);
      out.set(chunk.subarray(0, k), filled);
      filled += k;
      if (consume) {
        if (k === chunk.length) this._incoming.shift();
        else this._incoming[0] = chunk.subarray(k);
      } else index++;
    }
    if (consume) this._incomingLength -= n;
    return out;
  }

  _next() {
    if (this._frames.length) return Promise.resolve(this._frames.shift());
    if (this._lost) return Promise.reject(this._lost);
    return new Promise((resolve, reject) => { this._waiter = { resolve, reject }; });
  }

  _decode(reader, count) {
    try {
      const values = [];
      for (let i = 0; i < count; i++) values.push(reader.value());
      reader.finish();
      return values;
    } catch (e) {
      if (e instanceof Violation) throw this._violation(e.message);
      throw e;
    }
  }

  // Losing the worker (protocol.md section 8).

  _violationError(what) { return new WorkerError(`the worker broke the protocol: ${what}`); }
  _violation(what) { return this._lose(this._violationError(what)); }

  _lose(error) {
    if (this._lost || this._closed) return this._lost ?? error;
    this._lost = error;
    this._end();
    if (this._waiter) {
      this._waiter.reject(error);
      this._waiter = null;
    }
    return error;
  }

  _end() {
    this._stopTimer();
    this._worker?.terminate();
    this._signalLost();
    this._functions.clear();
    this._functionIds.clear();
    this._released.length = 0;
    this._failure = null;
    this._frames.length = 0;
    this._incoming.length = 0;
    this._output = this._loader = undefined;
  }

  _copyLost() {
    const error = this._lost instanceof Timeout ? new Timeout(this._lost.message)
      : new WorkerError(this._lost.message, this._lost.returncode);
    return error;
  }

  _startTimer(ms) {
    this._deadline = Date.now() + ms;
    this._timer = setTimeout(() => {
      this._lose(new Timeout(this._expired()));
    }, ms);
  }

  _expired() {
    return `the operation exceeded the timeout of ${this._timeout} ms`;
  }

  _stopTimer() {
    clearTimeout(this._timer);
    this._timer = null;
  }

  // Values.

  _reference(value) {
    if (value instanceof PyObject) {
      if (value._runtime !== this) throw new TypeError("the object belongs to another runtime");
      if (value._id === null) throw new TypeError("the object was released");
      return { handle: value._id };
    }
    if (value instanceof Named) return { fn: this._functionId(value.fn), name: value.name };
    if (typeof value === "function") return { fn: this._functionId(value), name: value.name || "function" };
    throw new TypeError(`cannot convert ${value?.constructor?.name ?? typeof value} to an engine value`);
  }

  _functionId(fn) {
    let id = this._functionIds.get(fn);
    if (id === undefined) {
      id = this._functions.size + 1;
      this._functionIds.set(fn, id);
      this._functions.set(id, fn);
    }
    return id;
  }

  _obtain(id) { return new PyObject(CREATE, this, id); }

  _release(id) {
    if (!this._lost && !this._closed) this._released.push(id);
  }

  // Errors from the engine.

  _checkError(error) {
    const kinds = { type: "string", message: "string", filename: "string", line: "number", token: "number", stop: "string" };
    const ok = error instanceof Map && error.size === 7 && Object.entries(kinds).every(([k, t]) => typeof error.get(k) === t)
      && (error.get("exception") === null || error.get("exception") instanceof PyObject);
    if (!ok) throw this._violation("malformed error");
  }

  _engineError(error) {
    if (error.get("stop") === "timeout") {
      this._failure = null;
      return new Timeout(this._expired());
    }
    let cause;
    if (this._failure && error.get("token") === this._failure.token) cause = this._failure.error;
    this._failure = null;
    return new PythonError(error.get("type"), error.get("message"), error.get("exception"), error.get("filename"),
      error.get("line"), cause === undefined ? undefined : { cause });
  }

  // Host callbacks (worker requests).

  async _serve(reader) {
    let run;
    try {
      if (reader.kind === wire.HOST) {
        const [fid, args, kwargs] = this._decode(reader, 3);
        const fn = this._functions.get(fid);
        if (fn === undefined || !Array.isArray(args) || !(kwargs instanceof Map) || [...kwargs.keys()].some((k) => typeof k !== "string"))
          throw this._violation("malformed host call");
        run = () => {
          if (fn[KEYWORDS]) return fn(...args, Object.assign(Object.create(null), Object.fromEntries(kwargs)));
          if (kwargs.size) throw new TypeError(`${fn.name || "function"}() takes no keyword arguments`);
          return fn(...args);
        };
      } else if (reader.kind === wire.LOAD) {
        const [name] = this._decode(reader, 1);
        if (typeof name !== "string") throw this._violation("malformed load");
        run = () => this._load(name);
      } else {
        const [text] = this._decode(reader, 1);
        if (typeof text !== "string") throw this._violation("malformed output");
        run = () => this._writeOutput(text);
      }
    } catch (e) {
      if (e instanceof WorkerError) throw e;
      run = () => { throw e; }; // read whole but not convertible: the engine gets the error
    }
    const remaining = this._timer !== null ? this._deadline - Date.now() : null;
    this._stopTimer();
    this._levels.push({ tail: Promise.resolve() });
    let reply;
    try {
      const result = await run();
      reply = wire.message(wire.RESULT, [result], (value) => this._reference(value));
    } catch (e) {
      if (this._lost) throw this._lost;
      reply = wire.message(wire.RAISE, [this._failureOf(e)], (value) => this._reference(value));
    } finally {
      this._levels.pop();
      if (remaining !== null && !this._lost) this._startTimer(remaining);
    }
    if (this._lost) throw this._lost;
    if (reply.length - 4 > this._messageLimit)
      reply = wire.message(wire.RAISE, [this._failureOf(new RangeError("message exceeds the limit"))], (value) => this._reference(value));
    await this._send(reply);
  }

  async _load(name) {
    if (!this._loader) return null;
    const source = await this._loader(name);
    if (source !== null && source !== undefined && typeof source !== "string")
      throw new TypeError("a loader must return a string or null");
    return source ?? null;
  }

  async _writeOutput(text) {
    if (!this._output) {
      const lines = (this._line + text).split("\n");
      this._line = lines.pop();
      for (const line of lines) console.log(line);
      return null;
    }
    try {
      await this._output(text);
    } catch (e) {
      console.error("Exception ignored in the runtime's output callback:", e);
      throw e;
    }
    return null;
  }

  _flushLine() {
    if (this._line) console.log(this._line);
    this._line = "";
  }

  _failureOf(error) {
    const token = ++this._tokens;
    this._failure = { token, error };
    if (error instanceof PythonError && error.exception instanceof PyObject && error.exception._runtime === this
        && error.exception._id !== null)
      return { raise: error.exception, token };
    const classes = [];
    if (error instanceof Error) {
      if (error.name) classes.push(error.name);
      for (let proto = Object.getPrototypeOf(error); proto && proto !== Object.prototype; proto = Object.getPrototypeOf(proto))
        if (proto.constructor?.name && !classes.includes(proto.constructor.name)) classes.push(proto.constructor.name);
    }
    const message = error instanceof Error ? error.message : String(error);
    return { classes: new Tuple(classes), args: new Tuple([message]), message, token };
  }

  // The public API.

  _noCallback(what) {
    if (this._levels.length > 1) throw new Error(`cannot ${what} while a host function of this runtime is running`);
  }

  /** Run source and resolve to the value of its last expression statement. */
  async eval(source, filename = "<string>") {
    this._noCallback("evaluate source");
    return this._run(wire.EVAL, [string(source), string(filename)]);
  }

  /** Run source for its effects. */
  async exec(source, filename = "<string>") {
    this._noCallback("evaluate source");
    await this._run(wire.EXEC, [string(source), string(filename)]);
  }

  /** Call a global name or a PyObject with positional and keyword arguments. */
  async call(target, args = [], kwargs = {}) {
    return this._run(wire.CALL, [target, new Tuple([...args]), kwargs]);
  }

  async get(name) { return this._run(wire.GET, [string(name)]); }

  async set(name, value) { await this._run(wire.SET, [string(name), value]); }

  async delete(name) { await this._run(wire.DELETE, [string(name)]); }

  /** Bind a function as the global name. */
  async define(name, fn) {
    if (typeof fn !== "function") throw new TypeError("define() needs a function");
    await this._run(wire.SET, [string(name), new Named(fn, name)]);
    return fn;
  }

  /** Make `import name` create a module from members, then source. */
  async registerModule(name, members = null, source = null) {
    if (source !== null && typeof source !== "string") throw new TypeError("source must be a string");
    await this._run(wire.MODULE, [string(name), members, source]);
  }

  /** Run the engine's cycle collector; resolves to the number of values freed. */
  async collect() { return this._run(wire.COLLECT, []); }

  get closed() { return this._closed || this._lost !== null; }

  /** End the Worker. Idempotent. */
  close() {
    if (this._closed) return;
    if (this._levels.length > 1) throw new Error("cannot close the runtime while a host function of this runtime is running");
    if (!this._lost) {
      this._closed = true;
      this._end();
      if (this._waiter) {
        this._waiter.reject(new Error("the runtime is closed"));
        this._waiter = null;
      }
    }
    this._closed = true;
  }

  [Symbol.dispose]() { this.close(); }
}

// The Worker script; tests point it at a fake.
Runtime._workerURL = new URL("./worker.js", import.meta.url);

/** A function passed in under a chosen name, as define() does. */
class Named {
  constructor(fn, name) { this.fn = fn; this.name = name; }
}

const COMPARE = { "<": 11, "<=": 12, "==": 13, "!=": 14, ">": 15, ">=": 16 };

/** An engine value held by the worker; every method is one message. */
export class PyObject {
  constructor(token, runtime, id) {
    if (token !== CREATE) throw new TypeError("PyObject values come from a Runtime");
    this._runtime = runtime;
    this._id = id;
    released.register(this, { runtime, id }, this);
  }

  async _op(op, ...operands) {
    if (this._id === null) throw new TypeError("the object was released");
    return this._runtime._run(wire.OP, [op, this, ...operands]);
  }

  async get(name) { return this._op(1, string(name)); }
  async set(name, value) { await this._op(2, string(name), value); }
  getItem(key) { return this._op(3, key); }
  async setItem(key, value) { await this._op(4, key, value); }
  len() { return this._op(5); }
  has(item) { return this._op(6, item); }
  async call(args = [], kwargs = {}) { return this._runtime._run(wire.CALL, [this, new Tuple([...args]), kwargs]); }
  bool() { return this._op(9); }
  hash() { return this._op(10); }
  async compare(op, other) {
    if (!Object.hasOwn(COMPARE, op)) throw new RangeError(`unknown comparison ${op}`);
    return this._op(COMPARE[op], other);
  }
  repr() { return this._op(17); }
  str() { return this._op(18); }
  dir() { return this._op(19); }

  async *[Symbol.asyncIterator]() {
    const iterator = await this._op(7);
    for (;;) {
      let value;
      try {
        value = await iterator._op(8);
      } catch (e) {
        if (e instanceof PythonError && e.type === "StopIteration") return;
        throw e;
      }
      yield value;
    }
  }

  /** Drop the worker's reference now. */
  release() {
    if (this._id === null) return;
    released.unregister(this);
    this._runtime._release(this._id);
    this._id = null;
  }
}

function string(value) {
  if (typeof value !== "string") throw new TypeError(`expected a string, not ${typeof value}`);
  return value;
}
