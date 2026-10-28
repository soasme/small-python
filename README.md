# Small Python

A small, embeddable Python-language engine in C11, inspired by QuickJS.
Commands and public APIs use the **spy** prefix: `spy`, `spyc`, `spy_*`,
`SPYContext`, and `libspy.a`. No CPython or third-party runtime dependency.
As in QuickJS, the core (`spy.c`) is the language alone; the standard layer
(`spy-std.c`) registers `sys`, `gc`, `weakref`, and the other built-in modules
for the `spy` command and any host that links it.

**Status:** conforms to the Core profile of
[PLS-315](docs/standards/3_15.md), the Python 3.15 core language: all 345
specification tests (validated on CPython 3.15) and all 112 TLA+ models pass.
The standard library is out of scope; see the
[manual](docs/smallpython.md#31-python-language-support) for host choices.

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
- [PLS-315, the Python Language Specification](docs/standards/3_15.md): a single-file, versioned
  specification of the Python 3.15 core language in the style of ECMA-262, with
  algorithms, intrinsic objects in place of library modules, host hooks, and
  Core, Host, and Extension profiles. Project draft, not an official PSF standard.
- [Upstream Cython baseline](docs/testing/cython.md): 343 passing and 11,107 failing
  discovered examples; 13 files need another adapter. Reproduce with
  `make upstream` followed by `make cython-report`.
- [Specification tests](tests/spec/README.md): test262-style, core-only tests
  of every clause of PLS-315, including CPython's language tests ported without
  their library dependencies; `make test-spec` runs them on spy, and
  `make test-spec-oracle` validates them against the pinned CPython 3.15.
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
