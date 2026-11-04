# Java artifacts

Status: specification and implementation for the Maven build in `java/`,
published to Maven Central by the `java` job of
`.github/workflows/publish.yml`.

## 1 Goals

1. Embed Small Python in a JVM program with one Maven dependency: no C
   library to install and no compiler at the user's end. The jars carry the
   native files for every supported platform.
2. Keep the engine plain C11 that knows nothing of Java. The JNI library
   compiles the same `spy.c` and `spy-std.c` the Makefile does, with one C
   file of glue.
3. Offer the two ways in of the Rust crates (`rust.md`) and the Go module
   (`go.md`): the engine in the JVM, for trusted code, and the engine in a
   worker process (`protocol.md`), for untrusted code.
4. Follow Java's conventions: unchecked exceptions, `AutoCloseable` with
   try-with-resources, the garbage collector for references, and reflection
   over records for conversion.

Not goals: the Foreign Function and Memory API (Java 22), which would raise
the baseline from Java 17; a JPMS `module-info`; Android.

## 2 Artifacts

The group is `io.github.soasme`, the namespace Maven Central verifies for
the GitHub account `soasme`. The version is the engine's.

| Artifact | Package | Role |
|---|---|---|
| `small-python` | `io.github.soasme.spy` | The engine in this process, through JNI. |
| `small-python-worker` | `io.github.soasme.spy.worker` | The parent side of the worker protocol, in pure Java. It runs the `spy-worker` executable the jar carries. |

The artifacts share no code and depend on nothing, so a program takes one,
the other, or both. Each package is its jar's `Automatic-Module-Name`, as
the JLS recommends a module be named after its principal package. Both
need Java 17.

Names follow the JLS conventions and the Java embeddings of Python that
came before (Jython's `PythonInterpreter` and `PyObject`, Jep's
`Interpreter`): the entry point is `Interpreter`, not the `Runtime` of the
other packages, which would hide `java.lang.Runtime`; the Python values
the packages model are `PyObject`, `PyTuple`, `PyDict`, `PySet`, and so
on, which do not hide `java.lang.Object` or `java.util.Set` either.

### 2.1 Native files

A jar carries its native files under `<package>/native/<platform>/`, where
the platform is named as the release archives name it: `linux-x86_64`,
`linux-arm64`, `macos-arm64`, `macos-x86_64`, and `windows-x86_64`, from
the JVM's `os.name` and `os.arch`.

| Artifact | File | Built from |
|---|---|---|
| `small-python` | `libspyjni.so`, `libspyjni.dylib`, `spyjni.dll` | `spy-jni.c`, `spy.c`, `spy-std.c`, compiled together into one shared library |
| `small-python-worker` | `spy-worker`, `spy-worker.exe` | the Makefile's `spy-worker` |

On first use in a process the file is written to
`small-python/<name>-<hash>` in the user's cache directory, chosen as
`rust.md` §4.1 chooses it, through a temporary file renamed into place;
the worker is made executable by its owner alone. An existing file is used
only while its bytes equal the jar's. The system property
`io.github.soasme.spy.library` names a JNI library to load instead, and
`Interpreter.Builder.worker(path)` a worker to run instead, for platforms
the jar lacks and deployments without a writable cache.

`make java-native` builds the files of this platform into `java/*/native/`,
which git ignores; the publish workflow builds those of every platform and
packs them together (§6). The jars also carry `LICENSE` and the licenses of
the tables the engine includes in `META-INF/licenses/`.

## 3 `small-python`

```java
try (Interpreter py = Interpreter.create()) {
    py.define("add", (rt, args) -> args.get(0, Long.class) + args.get(1, Long.class));
    long n = py.eval("add(40, 2)").as(Long.class); // 42
}
```

### 3.1 Interpreter

`Interpreter` owns one `SPYContext`. `create` registers the standard layer
(`spy_std_init`); `createBare` has only the core and its `builtins`. Both
send output to `System.out`, as the worker does.

| Method | C API |
|---|---|
| `eval(source)`, `exec(source)` | `spy_eval`, `spy_exec`, filename `<string>` |
| `get(name)`, `set(name, value)` | `spy_get_global`, `spy_set_global` |
| `function(name, f)`, `define(name, f)` | `spy_native` with a release callback, then `spy_set_global` |
| `registerModule(name, init)`, `execModule(module, source, filename)` | `spy_new_module`, `spy_exec_module` |
| `loadNative(name, path)` | `spy_std_load_native` |
| `setOutput(appendable)`, `setLoader(loader)` | `spy_set_output`, `spy_set_module_loader` |
| `mount(directory, path, readOnly)` | `spy_mount`; a null `path` is `NULL` |
| `setLimit(limit, n)`, `getLimit(limit)` | `spy_set_limit`, `spy_get_limit` |
| `setPolicy(policy)`, `checkPolicy(event, args...)` | `spy_set_policy` (throwing refuses), `spy_policy_check` |
| `stepsUsed()`, `setOptimize(level)`, `collect()` | the same names |
| `toValue(x)` | the conversions of §3.3 |
| `version()` (static) | `spy_version` |
| `close()` | `spy_context_free` |

Every method of an interpreter and of its values is `synchronized` on the
interpreter: a context is never entered by two threads at once, and a
host function, which runs on the calling thread, may call back into it.
After `close` every operation throws `IllegalStateException`. `close`
itself throws it from a host function, module initializer, loader,
output, or policy of the interpreter, as the engine is running beneath it.

`spy-jni.c` maps each C function to one static native method of the
package-private `Native` class, passing contexts and values as `long`
pointers. It keeps a weak global reference to the interpreter as the
context's opaque pointer and calls the interpreter's methods back for host
functions, module initialization, output, loading, and the policy; a host
function is a global reference released by `spy_native`'s release
callback. Strings cross as UTF-16 and are converted in C, so a lone
surrogate keeps its identity in both directions (§3.3).

### 3.2 Values

`PyObject` holds one reference to an engine value. A `java.lang.ref.Cleaner`
queues the reference when the object becomes unreachable, and the
interpreter releases the queue on the thread of its next operation: the
context is never touched by the cleaner's thread. After `close` the queue
is dropped, because `spy_context_free` frees every value itself.

A method of a `PyObject` passes its pointer to the engine, and a host
function the engine calls may release the queue; so every method keeps its
object reachable (`Reference.reachabilityFence`) until it returns, or a
temporary such as `py.eval("f").call(g)` could be released while it runs.
`tests/tla/SpyJava.tla` models these lifetimes.

Its methods are `as`, `toJava`, `getAttr`, `setAttr`, `getItem`, `setItem`,
`call`, `callKeywords`, `iterator` (it is an `Iterable<PyObject>`),
`truth`, `isNone`, `repr`, and `str`; `toString` is `str(value)`. A value
passed to another interpreter is refused with `ValueError`.

### 3.3 Conversion

`toValue` converts in; `as(type)` converts out.

| Java | Engine |
|---|---|
| `null` | `None`; out: for any type but a primitive one |
| `Boolean` | `bool` (out: only a `bool`) |
| `Long`, `Integer`, `Short`, `Byte`, `BigInteger` | `int`; beyond `int64` in, or the target's range out: `OverflowError`; out into `BigInteger`: any size |
| `Double`, `Float` | `float` (out: also an `int`) |
| `String`, `Character` | `str` |
| `byte[]` | `bytes` (out: also `bytearray` and any iterable of bytes) |
| `PyTuple` | `tuple` (out: any iterable) |
| other `List`s and object arrays | `list`; out: any iterable |
| `Map` | `dict` in the map's iteration order; out: any mapping |
| records | `dict` of the components; out: any mapping, ignoring unknown keys, missing components null, zero, or false |
| `PyObject` | itself |
| `HostFunction` | a builtin function |

A record's `List` and `Map` components decode their elements by their
declared type arguments. `toJava()` gives `null`, `Boolean`, `Long` (or
`BigInteger` beyond 64 bits), `Double`, `String`, `byte[]`, a `List` for a
list, `PyTuple`, and a `LinkedHashMap` for a dict, and the `PyObject`
itself for anything else, including instances of subclasses of those
types. A Java `String` is UTF-16: a lone surrogate in a Python `str` is a
lone `char`, but two adjacent lone surrogates, which Python keeps as two
code points, form one supplementary character in Java and come back as it.

A host function receives the interpreter and `Args`: the positional
arguments as a `List<PyObject>` and the keyword arguments as a
`Map<String, PyObject>`; `get(index, type)` decodes one, raising
`TypeError` when there are fewer, and `keyword(name, type, otherwise)` one
keyword.

### 3.4 Errors

`PythonException`, unchecked, is an exception in either direction:
`getType`, `getPythonMessage` (`spy_error_display`'s text), `getFilename`,
and `getLine`; `getMessage` is `Type: message`. An engine exception that
escapes is copied out and cleared. A `PythonException` thrown by a host
function, module init, loader, or policy raises its type and message
(`spy_error`); any other exception raises `RuntimeError`, or for a policy
`PermissionError`, with the exception's message. Nothing reaches C as a
Java exception: an `Error` such as `StackOverflowError` raises
`RuntimeError` too, and an output write that throws fails the `print` with
`OSError`. Source containing NUL raises `SyntaxError`; a name containing
NUL raises `ValueError`.

### 3.5 Trust

As `rust.md` §3.5: the engine runs in the JVM's address space. Use
`small-python` for code you trust; for anything else use
`small-python-worker`. `loadNative` trusts the library completely, as
`rust.md` §3.5 says. `System.load` is a restricted method from Java 24
on, so programs on the module path pass `--enable-native-access` for the
module, and those on the class path `--enable-native-access=ALL-UNNAMED`,
to silence the JVM's warning.

## 4 `small-python-worker`

The Java counterpart of the Python package (`python.md`), the
`small-python-worker` crate, and the Go package `worker`, on the same
worker and protocol.

```java
try (Interpreter py = Interpreter.builder().timeout(Duration.ofSeconds(5)).start()) {
    py.define("greet", (rt, args, kwargs) -> "hello " + args.get(0));
    Object v = py.eval("greet('spy')"); // "hello spy"
}
```

### 4.1 Interpreter

`Interpreter.builder()` takes `std`, `stepLimit`, `memoryLimit`,
`outputLimit`, `timeout`, `messageLimit`, `output`, `loader`, `policy`, and
`worker`, with the defaults and meaning of the Python package's arguments
(`python.md` §3.1); `start()` starts the worker as `protocol.md` §9
describes and sends `INIT`. `ProcessBuilder` gives the worker an empty
environment, working directory `/`, and only descriptors 0 to 2, but it
cannot start a process in a group of its own: a terminal's `SIGINT` (Ctrl+C)
reaches the worker as well as the JVM, which loses it.

| Method | Message |
|---|---|
| `eval(source)`, `exec(source)` | `EVAL`, `EXEC` |
| `call(name, args...)`, `callKeywords(function, args, kwargs)` | `CALL`; `function` is a global name, a `PyObject`, or a `PyFunction` |
| `get(name)`, `set(name, value)`, `delete(name)` | `GET`, `SET`, `DELETE` |
| `function(name, f)`, `define(name, f)` | none, then `SET` |
| `registerModule(name, members, source)` | `MODULE` |
| `mount(directory, path, readOnly)` | `MOUNT`, after resolving `directory` |
| `collect()`, `usage()` | `COLLECT`, `USAGE`: steps and memory |
| `PyObject`'s `getAttr`, `setAttr`, `getItem`, `setItem`, `len`, `contains`, `iterator`, `truth`, `hash`, `compare`, `repr`, `str`, `dir`, `call`, `callKeywords` | `OP` 1 to 19, `CALL`; the iterator ends at `StopIteration` |
| `version()`, `pid()`, `isClosed()`, `close()` | the `INIT` reply, the process id, state, closing |

Operations are `synchronized` on the interpreter. A host function is
`(rt, args, kwargs) -> result`, with the positional arguments as a
`List<Object>` and the keyword arguments as a `Map<String, Object>`;
through the interpreter it receives it may make nested requests, but
`eval`, `exec`, and `close` throw `IllegalStateException` there. `close`
closes the worker's input and waits up to a second for it to exit.

### 4.2 Values

Values cross as Java values, one per row of `protocol.md` §4: `null`,
`Boolean`, `Long` or `BigInteger`, `Double`, `PyComplex`, `String`,
`byte[]`, `PyByteArray`, `List` (list), `PyTuple`, `PySet`, `PyFrozenSet`,
`PyDict` (items in order), and `PyObject`. Sending also accepts `Integer`,
`Short`, `Byte`, `Float`, `Character`, object arrays, `Map`s in their
iteration order, and `PyFunction`; any other type fails with `TypeError`,
and content nested deeper than 200 levels with `RecursionError`, before
sending. Sets and dicts are kept as sequences, so the parent never hashes
what the worker sends. Strings are as in §3.3: a lone surrogate is a lone
`char`, and every Java string can be sent.

`PyObject` is a handle to an engine value. When the garbage collector finds
one unreachable, a `Cleaner` queues its id, released with the next message
(`RELEASE`). The notice is sent before that message is encoded, so a handle
the message carries, reachable until then, is released only after it.
Handles are equal only to themselves. `tests/tla/SpyJavaWorker.tla` models
the turns, handle releases, timeouts, and closing.

### 4.3 Errors

| Exception | Meaning |
|---|---|
| `PythonException` | An engine exception escaped: `getType`, `getPythonMessage`, `getFilename`, `getLine`, `getObject` (a `PyObject`), and `getCause`. |
| `WorkerException` | The worker was lost (`protocol.md` §8); `exitStatus()` is its exit status when it exited on its own, on Unix 128 plus the signal that ended it. |
| `OperationTimeoutException` | The operation ran past the timeout; the engine stopped it and the interpreter stays open, unless the worker did not stop within the grace period and was terminated. |
| `IllegalStateException`, `IllegalArgumentException` | Misuse: a closed interpreter, a value of another interpreter, a message over the limit, `eval` in a host function. |

What a host function throws becomes the failure of `protocol.md` §7.4: a
`PythonException` carrying an object of this interpreter re-raises it
unchanged; another `PythonException` raises its type name (the builtin
class, else `RuntimeError`); `IllegalStateException` and
`IllegalArgumentException` raise `ValueError`, and any other exception
`RuntimeError`, or for a policy `PermissionError` and for output `OSError`,
with its message. If that exception escapes, the resulting
`PythonException`'s cause is what the host function threw. An `Error`
thrown by a host function loses the worker and goes on unwinding. Once
lost, every request throws the same exception.

### 4.4 Timeouts

As `go.md` §4.5, with two daemon threads per interpreter in place of the
goroutines: a reader hands each frame over a `SynchronousQueue`, checking
its length against the limit before allocating, and a writer drains a
queue of two messages. The interpreter waits for both with the deadline of
the timeout plus a grace period of one second, extended by the time spent
in host functions, the loader, and output.

### 4.5 Security

As `rust.md` §4.6.

## 5 Building and testing

```sh
make test-java      # mvn verify in java/, after the one below
make java-native    # this platform's JNI library and worker, into java/*/native
```

`java-native` needs a JDK for `jni.h`: `JAVA_HOME`, or the `java` on
`$PATH`. The tests are the ports of the Go module's: conversion in both
directions, records and maps, exceptions and their lines, host functions
with errors, keywords, and `Error`s, modules, the loader and output, limits,
the policy, mounts (not on Windows, where the engine has no file system
support), threads taking turns, values of another interpreter,
closed interpreters, closing from a host function, and values the garbage
collector releases, including one whose method is still running; for the
worker, nested callbacks, causes, object operations and handle release, a
timeout that excludes host time, workers killed by `SIGSEGV`, `SIGABRT`,
and `SIGKILL`, an `Error` or `close` in a host function, a worker that cannot start,
and the sealed sandbox on macOS. Both check that the engine's version is
the artifacts'.

## 6 Publishing

Pushing a version tag `vX.Y.Z` runs the `java` jobs of
`.github/workflows/publish.yml`. One job per platform runs `make test-java`
and uploads its `native/` directories; Linux builds in a `manylinux_2_28`
container, so the JNI library needs only glibc 2.28, and links the worker
statically, as the release archives do; Windows builds with the runner's
MinGW-w64 GCC. A last job gathers every platform's files, checks that each
is there, and runs `mvn -P release deploy`, which adds the sources, the
javadoc, and the GPG signatures Maven Central requires and uploads them
through the Central Portal. A version already on Maven Central is skipped.

The workflow needs the `maven-central` environment with the secrets
`MAVEN_CENTRAL_USERNAME` and `MAVEN_CENTRAL_PASSWORD` (a Central Portal
user token for the verified namespace `io.github.soasme`), and
`MAVEN_GPG_PRIVATE_KEY` and `MAVEN_GPG_PASSPHRASE` (a key whose public half
is on a public key server).

## 7 Alternatives considered

1. **The Foreign Function and Memory API.** It needs no C glue, but only
   from Java 22; JNI reaches every maintained Java release.
2. **One artifact with both packages.** Simpler to publish, but every
   program would download both native files for five platforms.
3. **Compiling the native files on the user's machine**, as the Rust and Go
   packages do. Maven has no build scripts, and a Java user cannot be
   assumed to have a C compiler.
4. **`Runtime` as the entry point**, for symmetry with the other packages.
   It would hide `java.lang.Runtime` in every file that imports it.
5. **An explicit `close` on values.** Forgetting it leaks and calling it
   early fails; the cleaner, with a queue drained on the interpreter's own
   thread, is safe either way, as in the Go module.
