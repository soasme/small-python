# Small Python

A small, embeddable Python-language engine in C11, inspired by QuickJS.
Commands and public APIs use the **spy** prefix: `spy`, `spyc`, `spy_*`,
`SPYContext`, and `libspy.a`. No CPython or third-party runtime dependency.
As in QuickJS, the core (`spy.c`) is the language alone; the standard layer
(`spy-std.c`) registers `sys`, `gc`, `weakref`, and the other built-in modules
for the `spy` command and any host that links it.

**Status:** experimental subset. The target is the full Python 3.15 core
language; the current engine does not yet conform to it.

```sh
make
./spy examples/hello.py
./spy -c 'print(sum(range(10)))'
make test
```

- [Engine manual](docs/smallpython.md): usage, embedding, implementation, benchmarks.
- [Python binding](python/docs/README.md): `pip install ./python` (or
  `pip install small-python`) provides `small_python`, which runs Small Python
  from CPython and injects Python functions as host functions.
- [SLP-315 language standard](docs/standards/3_15.md): a single-file, versioned
  specification of the Python 3.15 core language in the style of ECMA-262, with
  algorithms, intrinsic objects in place of library modules, host hooks, and
  Core, Host, and Extension profiles. Project draft, not an official PSF standard.
- [Upstream Cython baseline](docs/testing/cython.md): 343 passing and 11,107 failing
  discovered examples; 13 files need another adapter. Reproduce with
  `make upstream` followed by `make cython-report`.
- [CPython 3.15 coverage](docs/testing/cpython.md): pinned development oracle,
  full upstream file inventory, dynamic case discovery, unchanged doctest
  examples, and 180 passing cases from twelve complete unittest modules, including
  99 checked subtests. Reproduce
  with `make oracle cpython-discover cpython-report test-cpython-unittest`.
- [Development instructions](AGENTS.md): architecture, naming, code taste, and
  requirements for honest upstream test evidence.

The engine includes argument binding, closures, global/nonlocal scopes, decorators,
properties, f-strings, native template strings, complex arithmetic, Unicode identifiers with NFKC
normalization, user-defined hashing, C3 inheritance, `super`, class construction
hooks, basic exceptions,
unpacking, comprehensions, generator functions and delegation, sequence slices,
native coroutines, asynchronous generators and context managers, host-loaded
modules and packages, async comprehensions, reference counting, and cycle
collection. Generator finalization and many other required features remain.
See the manual for limits.
