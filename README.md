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

## From Python

The [`small_python`](python/docs/README.md) package runs Small Python from
CPython. Each runtime is a separate interpreter, in a worker process of its
own, that sees only what you give it; an engine crash raises an exception
instead of taking your program down:

```sh
pip install small-python
```

```python
import small_python

with small_python.Runtime() as rt:
    @rt.function
    def lookup(key):
        return {"answer": 42}.get(key)

    print(rt.eval("lookup('answer') * 2"))  # 84
```

## From Rust

The crates in [`rust/`](docs/packaging/rust.md) compile the engine from
source with `cc` during `cargo build`, so there is nothing to install.
`small-python` runs the engine in your process with a safe API (and serde
conversions); `small-python-worker` runs each runtime in a sandboxed worker
process, as the Python package does. [`examples/todo`](examples/todo)
is a Flask-style Python application served by axum, with JSON from serde.

```rust
let rt = small_python::Runtime::new()?;
rt.define("add", |rt, args| {
    let (a, b): (i64, i64) = args.extract()?;
    rt.to_py(a + b)
})?;
let n: i64 = rt.eval("add(40, 2)")?;  // 42
```

## Testing

```sh
make test         # C API tests and the specification suite
make test-spec    # specification tests only
make sanitize     # AddressSanitizer, leak, and undefined-behavior checks
make fuzz         # libFuzzer targets for FUZZ_SECONDS each
make bench        # startup benchmark
make test-rust    # the Rust crates and the todo example
```

## Documentation

- [Manual](docs/manual.md): usage, embedding, internals, benchmarks
- [Benchmarks](docs/benchmark.md): comparison with other Python engines
- [PLS-315](docs/standards/3_15.md): the language specification
- [Standard modules](docs/standards/std.md): the `sys` and `gc` modules, after CPython 3.15
- [Building programs](docs/build.md): the `spyc` bundler
- [Specification tests](tests/spec/README.md)
- [Cython compatibility baseline](docs/testing/cython.md)
- [Contributing](AGENTS.md): architecture and code style

## License

[MIT](LICENSE). Third-party notices, including CPython's and Unicode's, are in
[`docs/licenses`](docs/licenses).
