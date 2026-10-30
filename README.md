# Small Python

A small, embeddable Python engine written in C11.

Small Python runs Python 3.15 code with nothing but a C compiler and the C
standard library. It is built like [QuickJS](https://bellard.org/quickjs/):
a few C files, one header to embed, and a plain Makefile. CPython is not
needed to build or run it.

```sh
$ make
$ ./spy -c 'print(sum(range(10)))'
45
```

## Features

- **The Python 3.15 core language**: arbitrary-precision integers, Unicode,
  classes and metaclasses, generators, `async`/`await`, pattern matching,
  f-strings, and template strings.
- **Embeddable**: one header, `spy.h`, and one library, `libspy.a`. Each
  context is independent, with no global state.
- **Automatic memory management**: reference counting plus a cycle collector.
- **Standalone executables**: `spyc` turns a `.py` file into a C program.
- **Sandboxed files**: scripts can only `open` the directories the host mounts.
- **Packages** for [Python, JavaScript, Rust, and Go](#packages), each able to
  run untrusted code in a sandboxed worker.
- **Fast startup**: about 260 µs to create a context, run hello world, and
  tear it down (Apple M2, `-O2`).

## Conformance

Small Python implements the Core profile of [PLS-315](docs/standards/3_15.md),
a written specification of the Python 3.15 core language. All 357
specification tests and all 112 TLA+ models pass. Each test is also checked
against CPython 3.15.

Small Python implements the language and its builtins. The standard library
is out of scope.

PLS-315 is a project document, not an official PSF standard.

## Getting started

Build the interpreter, generator, and library:

```sh
make
```

Run a script or the interactive shell:

```sh
./spy examples/hello.py
./spy -i
```

Compile a script into a standalone program:

```sh
./spyc -o hello.c examples/hello.py
cc -std=c11 -Os -I. hello.c spy.c -lm -o hello
./hello
```

## Embedding

```c
#include "spy.h"
#include <stdio.h>

static SPYValue *square(SPYContext *c, size_t argc, SPYValue *const *argv, void *data) {
    int64_t n;
    if (spy_as_int(c, argv[0], &n)) return NULL;
    return spy_int(c, n * n);
}

int main(void) {
    SPYContext *c = spy_context_new();
    spy_define(c, "square", square, NULL);

    SPYValue *result = spy_eval(c, "square(12)", "<embed>");
    int64_t n;
    if (result && !spy_as_int(c, result, &n))
        printf("%lld\n", (long long)n);   /* 144 */

    spy_release(result);
    spy_context_free(c);
}
```

See [`examples/embed.c`](examples/embed.c) for the version with error
handling, and the [manual](docs/manual.md#34-c-api) for the full API.
[`examples/pong`](examples/pong) is a raylib game whose logic is Python,
calling a `raylib` module the host registers with `spy_new_module`
(`brew install raylib`, then `make -C examples/pong run`).
[`examples/flappy`](examples/flappy) goes further: `spyc` bundles its
game package, dynamically imported themes, and sprite, and links them with
the engine and a static raylib into one executable
(`make -C examples/flappy run`).

## Packages

Small Python is also packaged for four host languages. Every package can run
each runtime in a sandboxed *worker* of its own, which sees only the
functions, modules, and directories you give it: an engine crash, or code
exploiting one, fails the operation instead of taking your program down.
Rust and Go can also run the engine in your process, for trusted code and
the lowest overhead.

| Language | Install | In-process | Sandboxed worker | Documentation |
|---|---|---|---|---|
| Python 3.10+ | `pip install small-python` | | `small_python` | [python/docs](python/docs/README.md), [spec](docs/packaging/python.md) |
| JavaScript (Node.js 20+, browsers) | `npm install small-python` | | `small-python` (WebAssembly) | [javascript](javascript/README.md), [spec](docs/packaging/javascript.md) |
| Rust | `cargo add small-python` | `small-python` | `small-python-worker` | [crates](rust/small-python/README.md), [spec](docs/packaging/rust.md) |
| Go 1.24+ | `go get github.com/soasme/small-python/go` | `spy` | `worker` | [go](go/README.md), [spec](docs/packaging/go.md) |

The workers share one [protocol](docs/packaging/protocol.md) and one C
file, `spy-worker.c`: a process sealed by the OS sandbox for Python, Rust,
and Go, and a WebAssembly instance in a Worker thread for JavaScript. All of
them bound steps, memory, and time.

### Python

```python
import small_python

with small_python.Runtime(memory_limit=64 << 20, timeout=5) as rt:
    @rt.function
    def lookup(key):
        return {"answer": 42}.get(key)

    print(rt.eval("lookup('answer') * 2"))  # 84
```

### JavaScript

```js
import { Runtime } from "small-python";

const rt = await Runtime.create({ memoryLimit: 64 << 20, timeout: 5000 });
await rt.define("fetchUser", async (id) => ({ id, name: "Ada" }));
console.log(await rt.eval("fetchUser(7)['name'].upper()"));  // ADA
rt.close();
```

### Rust

The crates compile the engine from source with `cc` during `cargo build`,
so there is nothing to install. `small-python` has a safe API with optional
serde conversions; [`examples/todo`](examples/todo) is a Flask-style Python
application served by axum.

```rust
let rt = small_python::Runtime::new()?;
rt.define("add", |rt, args| {
    let (a, b): (i64, i64) = args.extract()?;
    rt.to_py(a + b)
})?;
let n: i64 = rt.eval("add(40, 2)")?;  // 42
```

### Go

`spy` compiles the engine with cgo; `worker` is pure Go and runs the
`spy-worker` executable that `make install` installs.

```go
rt, _ := spy.New()
defer rt.Close()
rt.Define("add", func(rt *spy.Runtime, args spy.Args) (any, error) {
	var a, b int
	err := args.Scan(&a, &b)
	return a + b, err
})
n, _ := spy.As[int](rt.Eval("add(40, 2)"))  // 42
```

## Testing

```sh
make test             # C API tests and the specification suite
make test-spec        # specification tests only
make sanitize         # AddressSanitizer, leak, and undefined-behavior checks
make fuzz             # libFuzzer targets for FUZZ_SECONDS each
make bench            # startup benchmark
make test-binding     # the Python package
make test-javascript  # the JavaScript package (wasi-sdk rebuilds its worker)
make test-rust        # the Rust crates and the todo example
make test-go          # the Go module
```

## Documentation

- [Manual](docs/manual.md): usage, embedding, internals, benchmarks
- [Benchmarks](docs/benchmark.md): comparison with other Python engines
- [PLS-315](docs/standards/3_15.md): the language specification
- [Standard modules](docs/standards/std.md): the `sys` and `gc` modules, after CPython 3.15
- [CPython's Lib](docs/python-lib.md): scope of running CPython's `Lib/` unchanged
- [Building programs](docs/build.md): the `spyc` bundler
- Packages: [Python](docs/packaging/python.md), [JavaScript](docs/packaging/javascript.md), [Rust](docs/packaging/rust.md), [Go](docs/packaging/go.md), and the [worker protocol](docs/packaging/protocol.md) they share
- [Specification tests](tests/spec/README.md)
- [Cython compatibility baseline](docs/testing/cython.md)
- [Contributing](AGENTS.md): architecture and code style

## License

[MIT](LICENSE). Third-party notices, including CPython's and Unicode's, are in
[`docs/licenses`](docs/licenses).
