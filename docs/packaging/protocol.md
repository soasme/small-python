# Worker protocol

Status: specification. The packages in `python.md` and `javascript.md`, the
`small-python-worker` crate in `rust.md`, and the Go package `worker` in
`go.md` run the engine through this protocol; none links the engine into
its host.

## 1 Purpose

The engine is C. A memory-safety bug in it, or in code that exploits one,
must not crash or take over the program embedding it. The packages therefore
run each runtime in a *worker*, a separate address space that owns exactly one
`SPYContext`, and talk to it over a byte stream. The embedding program (the
*parent*) trusts itself and nothing the worker says.

| Package | Worker | Stream | Separation |
|---|---|---|---|
| Python | `spy-worker` executable, one process per runtime | the worker's stdin and stdout pipes | OS process |
| Rust (`small-python-worker`) | as Python | as Python | OS process |
| Go (`worker`) | as Python | as Python | OS process |
| JavaScript | `spy-worker.wasm` in a Worker thread, one per runtime | `postMessage` out, a `SharedArrayBuffer` in | WebAssembly sandbox and a Worker thread |

Both workers are built from the same C file, `spy-worker.c`, with only the
stream functions differing. Everything below holds for both.

## 2 Trust model

1. The parent trusts its own code, its host functions, and its callbacks.
2. The parent treats every byte from the worker as hostile. A worker that
   breaks a rule of this document (a malformed message, an unknown function
   id, a message over the size limit, a reply out of turn) is terminated, and
   the operation fails with a worker error (§8). Decoding never trusts a
   length, a count, a nesting depth, or an id it has not checked.
3. The worker trusts the parent. On a malformed message from the parent it
   exits with status 3.
4. Engine code reaches the parent only through what the parent registered:
   host functions, the module loader, and output. A compromised worker can
   call those with arbitrary arguments, and nothing else. Host functions are
   therefore the security boundary the embedder writes, as they are for
   uncompromised engine code.
5. A worker never outlives its parent's interest: it exits when its input
   stream ends and, for a process, when the parent process dies (§9).

## 3 Framing

A message is a 4-byte little-endian unsigned length `n` followed by `n` bytes
of payload. `n` is at least 1 and at most the *message limit* (default
64 MiB, configurable by the parent and sent in `INIT`, §7.5). A message over the
limit is a protocol violation for either side.

The payload is one *kind* byte followed by that kind's fields, encoded as in
§4. The whole payload must be consumed; trailing bytes are a violation.

A side never sends a message over the limit. When a value it must send would
exceed it, the parent raises its own error before sending, and the worker
raises `OverflowError("message exceeds the limit")` in the engine; a reply
that cannot be sent becomes a `RAISE` of that error instead.

## 4 Values

A value is a tag byte followed by its contents. Integers in lengths and counts
are 4-byte little-endian unsigned (`u32`); ids are 8-byte little-endian
unsigned (`u64`).

| Tag | Value | Contents |
|---|---|---|
| `N` | `None` | — |
| `F`, `T` | `False`, `True` | — |
| `i` | `int` in signed 64 bits | 8 bytes, little-endian two's complement |
| `I` | any other `int` | `u32` length, then ASCII: optional `-`, then `0x` and lowercase hex digits without leading zeros |
| `f` | `float` | 8 bytes, IEEE 754 binary64, little-endian |
| `c` | `complex` | two binary64 values, real then imaginary |
| `s` | `str` | `u32` length, then the code points in UTF-8, where a lone surrogate is encoded as its three-byte sequence (CPython's `surrogatepass`) |
| `b` | `bytes` | `u32` length, then the bytes |
| `B` | `bytearray` | as `b` |
| `l`, `t` | `list`, `tuple` | `u32` count, then that many values |
| `S`, `z` | `set`, `frozenset` | `u32` count, then that many values |
| `d` | `dict` | `u32` count, then that many key and value pairs, in order |
| `h` | engine value by reference | `u64` handle id (worker to parent only) |
| `p` | parent function | `u64` function id, then a `str` value naming it (parent to worker only) |

Rules:

1. Only values whose engine type is *exactly* one of the types above are sent
   by content. Instances of subclasses (a `dict` subclass, an `int` subclass
   other than `bool`, a `str` subclass) are sent as handles, so a subclass's
   overridden behavior is never bypassed by copying its storage. `bool` is
   its own tag.
2. Values nest at most 200 levels below a message field. A side asked to
   send deeper content fails the conversion with `RecursionError` (the worker
   raises it in the engine); a receiver treats deeper content as a violation.
3. Containers are copied. A container reachable twice is sent twice; a
   container that contains itself reaches the depth limit.
4. `I` is used only when `i` cannot hold the value. A decoder rejects an `I`
   value that fits in `i`, leading zeros, uppercase digits, or `-0x0`.
5. A `str` must decode as UTF-8 with `surrogatepass`; anything else, such as
   an overlong form or a truncated sequence, is a violation. Two adjacent
   surrogate sequences are two code points, as in CPython.
6. A `d` key or an `S`/`z` element that the receiving side cannot hash fails
   the conversion, not the protocol. The parent raises its own error; the
   worker raises `TypeError` in the engine.
7. A worker never sends `p`. A parent function that comes back from the engine
   arrives as a handle to the engine's native function.

## 5 Handles

The worker keeps a table from handle id to an owned engine reference. Every
`h` it sends creates a new entry with a new id; ids start at 1, increase by
one, and are never reused within a worker's life, so a stale id cannot name a
different value.

The parent owns each id it receives and must eventually send it back in
`RELEASE`. Ids received in a message the parent rejects need no release: the
worker is terminated. Sending a released or unknown id is a parent bug; the
worker exits with status 3.

Function ids name the parent's table of callables. The parent assigns them,
keeps the callable until the runtime ends, and sends the same id for the same
callable object. The worker turns each `p` into one engine native function per
id, reused for later appearances of the id; the native keeps the name from
the first appearance.

## 6 Turns

Exactly one side holds the *turn*. The parent starts with it. Communication is
a strict stack of requests:

1. The side holding the turn may send a request; the turn passes to the other
   side.
2. The side receiving a request handles it. While handling it, it may send
   nested requests of its own (each passes the turn back, and returns it with
   a reply). It finishes by sending exactly one reply, which returns the turn.
3. A reply always answers the innermost outstanding request. No request ids
   are needed.
4. A notice (`RELEASE`) is sent only by the side holding the turn and does not
   pass the turn.

The worker sends a request only while handling one from the parent; it has no
activity of its own. So neither side ever writes while the other may write,
and a full pipe cannot deadlock.

## 7 Messages

Fields are listed in order; each is a value (§4).

### 7.1 Parent to worker

| Kind | Name | Fields | Reply value |
|---|---|---|---|
| `0x01` | `INIT` | `options` dict (§7.5) | `str`: the engine version |
| `0x02` | `EVAL` | `source` str, `filename` str | the result |
| `0x03` | `EXEC` | `source` str, `filename` str | `None` |
| `0x04` | `CALL` | `target`, `args` tuple, `kwargs` dict | the result |
| `0x05` | `GET` | `name` str | the global, else builtin |
| `0x06` | `SET` | `name` str, `value` | `None` |
| `0x07` | `DELETE` | `name` str | `None` |
| `0x08` | `MODULE` | `name` str, `members` dict or `None`, `source` str or `None` | `None` |
| `0x09` | `MOUNT` | `directory` str, `path` str, `read_only` bool | `None` |
| `0x0a` | `COLLECT` | — | `int` freed |
| `0x0b` | `OP` | `op` int, `target`, operands (§7.3) | the result |
| `0x0c` | `RELEASE` | `ids` tuple of `int` | notice: no reply |

`CALL`'s target is a global name (`str`, looked up like `GET`) or a handle
sent back as `h`. A parent sends `h` only for ids it holds.

`SET` with a `p` value is how a parent defines a host function.

`MODULE` registers `name` with `spy_new_module`. On first import the worker
sets each member as an attribute, then runs `source` in the module with
filename `<name>`. Registering a name again replaces it.

`EVAL` and `EXEC` raise `SyntaxError` in the engine for source containing a
NUL character.

`MOUNT` passes an absolute host directory and an absolute engine path to
`spy_mount`. The parent resolves both; the worker does not consult its own
working directory.

`RELEASE` drops the listed handles.

### 7.2 Worker to parent

| Kind | Name | Fields | Reply value |
|---|---|---|---|
| `0x21` | `HOST` | `function` int, `args` tuple, `kwargs` dict | the result |
| `0x22` | `LOAD` | `name` str | `str` source, or `None` when absent |
| `0x23` | `OUTPUT` | `text` str | `None` |

`LOAD` names are what the engine's loader receives, including the
`.__init__` and `.__namespace__` probes; the parent maps them onto its loader
(`python.md` §3.5).

A `RAISE` reply to `OUTPUT` makes the engine's write fail with its own
`OSError`; the parent reports the cause on its side.

### 7.3 Object operations

`OP` applies one engine operation to the handle `target`. Operations use
engine builtins captured when the worker started, so engine code rebinding
`len` or `getattr` cannot change them.

| `op` | Operation | Operands | Result |
|---|---|---|---|
| 1 | `getattr(t, name)` | `name` str | value |
| 2 | `setattr(t, name, v)` | `name` str, `v` | `None` |
| 3 | `t[k]` | `k` | value |
| 4 | `t[k] = v` | `k`, `v` | `None` |
| 5 | `len(t)` | — | `int` |
| 6 | `x in t` | `x` | `bool` |
| 7 | `iter(t)` | — | value |
| 8 | `next(t)` | — | value; at the end, a `RAISE` of type `StopIteration` |
| 9 | `bool(t)` | — | `bool` |
| 10 | `hash(t)` | — | `int` |
| 11–16 | `t < o`, `<=`, `==`, `!=`, `>`, `>=` | `o` | value |
| 17 | `repr(t)` | — | `str` |
| 18 | `str(t)` | — | `str` |
| 19 | `dir(t)` | — | `list` |

### 7.4 Replies

| Kind | Name | Fields |
|---|---|---|
| `0x40` | `RESULT` | `value` |
| `0x41` | `RAISE` | worker: `error` (below); parent: `failure` (below) |

A worker's `error` is a dict with exactly these keys:

| Key | Value |
|---|---|
| `type` | `str`: `spy_error_type`, the class name, qualified by its module unless it is a builtin |
| `message` | `str`: `spy_error_display`, the text CPython's traceback shows after the type |
| `filename`, `line` | `str` and `int`: where it was raised |
| `exception` | handle to the exception, or `None` when it could not be obtained |
| `token` | `int`: the `token` of the parent `failure` this exception came from unchanged, or 0 |

A parent's `failure` (to `HOST`, `LOAD`, or `OUTPUT`) is a dict of one of
two shapes. To re-raise an engine exception unchanged (a host function let an
engine exception of the same runtime escape):

| Key | Value |
|---|---|
| `raise` | handle of the exception |
| `token` | `int`: a parent-chosen nonzero number naming this failure |

Otherwise, to raise a new exception:

| Key | Value |
|---|---|
| `classes` | `tuple` of `str`: the parent exception's class names, most derived first |
| `args` | `tuple`: its arguments, or `None` when they do not convert |
| `message` | `str`: its text, used when `args` is `None` |
| `token` | as above |

When a host function's result does not convert, the parent replies with a
failure for its own `TypeError` instead.

For the second shape the worker raises the first name in `classes` that is a
class in the engine's `builtins` module as the worker found it at start (a
rebound name does not count), falling back to `RuntimeError`, called with
`args` or `(message,)`; if that call fails, it raises `RuntimeError(message)`. It remembers the token
with the exception object it raised; if that same object escapes the
operation, its `error` carries the token.

### 7.5 `INIT` options

`INIT` is the first message and is sent once, with exactly these keys.

| Key | Value | Effect |
|---|---|---|
| `std` | `bool` | register the standard modules with `spy_std_init` |
| `step_limit` | `int` ≥ 0 | `spy_set_step_limit`; 0 is unlimited |
| `memory_limit` | `int` ≥ 0 | bytes the engine may hold allocated; 0 is unlimited (§10) |
| `message_limit` | `int` from 1 to 2³²−1 | the limit of §3, for both directions |

The worker always installs output and a module loader that send `OUTPUT` and
`LOAD`; a parent without a loader answers `None`.

## 8 Losing the worker

The parent terminates the worker (`SIGKILL`, or `Worker.terminate()`) and
marks the runtime *lost* when any of these happen:

1. a protocol violation (§2);
2. the stream ends or the worker exits: a crash, an `abort`, an OS limit;
3. the timeout of the current operation expires (§10);
4. an exception interrupts the parent while it waits for the worker, such as
   `KeyboardInterrupt` in Python.

The operation in progress fails with the package's worker error, naming the
cause (exit status or signal for 2). Every later operation, including those of
objects from the runtime, raises the same kind of error. Releasing handles of
a lost runtime does nothing. Nothing is restarted: the state of a lost runtime
is gone, and a new runtime must be made.

## 9 Process hygiene (native worker)

The worker is started with an empty environment, working directory `/`, no
inherited descriptors besides 0, 1, and 2, and in its own process group, so a
terminal's `SIGINT` (Ctrl+C on Windows) reaches only the parent. At start it:

1. moves the protocol to two fresh descriptors (in binary mode on Windows) and
   points 0 at `/dev/null` (`NUL`) and 1 at 2, so a stray write to stdout
   cannot corrupt the stream;
2. sets `RLIMIT_CORE` to 0, or on Windows turns off crash dialogs;
3. arranges to die with its parent: `prctl(PR_SET_PDEATHSIG, SIGKILL)` on
   Linux, a thread waiting on the parent with `kqueue` `NOTE_EXIT` on macOS,
   and a thread waiting on the parent's process handle on Windows. It also
   exits when its input stream ends.

Diagnostics from a crashing worker (an assertion, a sanitizer report) go to
the inherited stderr.

Before it handles its first `EVAL`, `EXEC`, `CALL`, or `OP`, which are the
requests that can run engine code, the worker *seals* itself under the
platform's OS sandbox (`python.md` §4), allowing files only beneath the
directories mounted so far. A `MOUNT` after sealing raises `PermissionError`
in the engine. Only after sealing can code the parent did not write run in
the worker.

## 10 Limits

| Limit | Enforced by | Effect when exceeded | Runtime survives |
|---|---|---|---|
| steps | engine step counter | `RuntimeError` in the engine | yes |
| memory | the worker's allocator | `MemoryError` in the engine | yes |
| recursion | engine frame and C stack guards | `RecursionError` in the engine | yes |
| time | parent, wall clock | worker terminated | no |
| message size | both sides | worker terminated | no |

The memory limit counts every byte the engine requests through
`malloc`/`calloc`/`realloc` (the worker builds the engine with those names
mapped to a counting allocator) and refuses requests that would exceed it.
The worker's own protocol buffers are not counted. In WebAssembly the linear
memory's maximum is an additional hard bound.

The timeout counts only time the parent spends waiting for the worker within
one top-level operation. Time inside host functions, the loader, and output is
the parent's own and is not counted.

## 11 Versioning

The parent and worker ship together in one package and are never mixed. The
`INIT` reply carries the engine version for diagnostics only; the protocol has
no negotiation.
