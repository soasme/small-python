# Small Python for Java

Run [Small Python](https://github.com/soasme/small-python), a small Python
3.15 engine written in C11, from Java 17 or later. Each interpreter is a
separate engine with its own globals and modules. The code it runs sees
only what you hand it: builtins, the functions and modules you define for
it, and the directories you mount. It cannot reach your Java objects,
files, network, or environment unless a function of yours does so for it.

```xml
<dependency>
  <groupId>io.github.soasme</groupId>
  <artifactId>small-python-worker</artifactId> <!-- or small-python -->
  <version>0.6.0</version>
</dependency>
```

```java
import io.github.soasme.spy.worker.Interpreter;

try (Interpreter py = Interpreter.builder().timeout(Duration.ofSeconds(5)).start()) {
    py.define("greet", (rt, args, kwargs) -> "hello " + args.get(0));
    Object v = py.eval("greet('spy')"); // "hello spy"
}
```

The jars carry the native code for Linux (x86-64, arm64, glibc 2.28 or
later), macOS (arm64, x86-64), and Windows (x86-64); nothing needs to be
installed.

## Choosing an artifact

| | `small-python` | `small-python-worker` |
|---|---|---|
| Package | `io.github.soasme.spy` | `io.github.soasme.spy.worker` |
| Where the engine runs | in the JVM, through JNI | in a `spy-worker` process of its own, sealed by the OS sandbox |
| For | code you trust: configuration, rules, plugins you ship | code you do not: users' scripts, code written by a language model |
| An engine crash | crashes the JVM | fails the operation with `WorkerException` |
| Values | references (`PyObject`) to engine objects | copies, plus `PyObject` handles |
| Bounding a run | step, memory, and output limits | step, memory, output, and time limits |
| Cost of a call | a JNI call | a message over a pipe |

Both run the same engine and the same Python. Start with the worker when
in doubt; move to `small-python` when you trust the code and the overhead
matters.

## In-process: `small-python`

```java
import io.github.soasme.spy.Interpreter;

try (Interpreter py = Interpreter.create()) {        // createBare(): no sys
    py.exec("def area(w, h):\n    return w * h");
    long n = py.eval("area(3, 4)").as(Long.class);    // 12
    py.set("limit", 10);
    PyObject limit = py.get("limit");
}
```

### Values

A `PyObject` is a reference to an engine value; the garbage collector
releases it. Its methods do what Python does: `getAttr`, `setAttr`,
`getItem`, `setItem`, `call`, `callKeywords`, iteration (it is an
`Iterable<PyObject>`), `truth`, `isNone`, `repr`, and `str`.

```java
for (PyObject square : py.eval("(n * n for n in range(4))")) {
    System.out.println(square.as(Long.class));
}
String upper = py.eval("str.upper").call("spy").as(String.class); // "SPY"
```

Anything you pass in converts with `py.toValue`; `as(type)` and `toJava()`
convert out:

| Java | Python |
|---|---|
| `null` | `None` |
| `Boolean` | `bool` |
| `Long`, `Integer`, `Short`, `Byte`, `BigInteger` | `int` (out of the target's range: `OverflowError`) |
| `Double`, `Float` | `float` |
| `String`, `Character` | `str` |
| `byte[]` | `bytes` (out: also `bytearray`) |
| `PyTuple` | `tuple` |
| other `List`s, object arrays | `list` (out: any iterable) |
| `Map` | `dict`, in iteration order (out: any mapping) |
| records | `dict` of the components (out: any mapping) |
| `HostFunction` | a builtin function |

```java
record User(String name, List<String> roles) {}

py.set("user", new User("ada", List.of("dev")));
User u = py.eval("user | {'name': user['name'].title()}").as(User.class);
```

`toJava()` gives `null`, `Boolean`, `Long` or `BigInteger`, `Double`,
`String`, `byte[]`, `List`, `PyTuple`, and `Map` for those types, and the
`PyObject` itself for anything else.

### Host functions, modules, output

```java
py.define("greet", (rt, args) ->
        "hello " + args.get(0, String.class) + args.keyword("end", String.class, "!"));
py.registerModule("config", (rt, module) -> {
    module.setAttr("region", "eu");
    rt.execModule(module, "def describe(): return 'region ' + region", "<config>");
});
py.setLoader(name -> sources.get(name));            // null: no such module
StringBuilder out = new StringBuilder();
py.setOutput(out);                                  // System.out by default
py.mount(Path.of("/srv/reports"), "/data", true);   // open() reaches only this
```

A host function that throws `new PythonException("KeyError", "missing")`
raises `KeyError` in the engine; any other exception raises `RuntimeError`
with its message.

### Limits and policy

```java
py.setLimit(Limit.STEPS, 1_000_000);
py.setLimit(Limit.MEMORY, 64 << 20);
py.setPolicy((event, args) -> {                     // "open", "import", "exec", "input"
    if (event.equals("open")) throw new SecurityException("no files");
});
```

### Errors and threads

An engine exception arrives as `PythonException`, unchecked, with
`getType()`, `getPythonMessage()`, `getFilename()`, and `getLine()`. An
interpreter and its values may be used from any thread; operations take
turns. A closed interpreter throws `IllegalStateException`.

On Java 24 and later, pass `--enable-native-access=ALL-UNNAMED` (or the
module's name) to the JVM to silence the warning about `System.load`.

## Sandboxed: `small-python-worker`

```java
Interpreter py = Interpreter.builder()
        .stepLimit(1_000_000)
        .memoryLimit(64 << 20)
        .outputLimit(1 << 20)
        .timeout(Duration.ofSeconds(5))
        .output(out)
        .loader(sources::get)
        .policy((event, args) -> {})
        .start();
```

Values cross by copy: `null`, `Boolean`, `Long` or `BigInteger`, `Double`,
`PyComplex`, `String`, `byte[]`, `PyByteArray`, `List`, `PyTuple`,
`PySet`, `PyFrozenSet`, and `PyDict`. Anything else stays in the worker as
a `PyObject` handle, whose methods (`getAttr`, `getItem`, `len`,
`contains`, iteration, `compare`, `call`, ...) are requests to it.

```java
py.exec("class Point:\n    def __init__(self, x): self.x = x");
PyObject point = (PyObject) py.eval("Point(3)");
long x = (Long) point.getAttr("x");                 // 3
```

| Exception | Meaning |
|---|---|
| `PythonException` | An engine exception; `getObject()` is the exception in the worker, and `getCause()` what your host function threw, if that escaped. |
| `OperationTimeoutException` | The operation ran past the timeout; the interpreter stays usable. |
| `WorkerException` | The worker crashed or misbehaved; the interpreter is gone. |

A host function receives `(rt, args, kwargs)` and may call back into the
interpreter, except for `eval` and `exec`. The worker seals itself under
the OS sandbox before it runs code, so mount directories first.

## Development

```sh
make test-java      # build this platform's native files and run mvn verify
```

The specification is [docs/packaging/java.md](https://github.com/soasme/small-python/blob/main/docs/packaging/java.md);
the worker protocol is [docs/packaging/protocol.md](https://github.com/soasme/small-python/blob/main/docs/packaging/protocol.md).
