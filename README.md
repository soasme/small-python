# slim.py

A small, embeddable Python-language engine in C11, inspired by QuickJS.
Commands and public APIs use the **spy** prefix: `spy`, `spyc`, `spy_*`,
`SPYContext`, and `libspy.a`. No CPython or third-party runtime dependency.

**Status:** experimental subset. The target is the full Python 3.15 core
language; the current engine does not yet conform to it.

```sh
make
./spy examples/hello.py
./spy -c 'print(sum(range(10)))'
make test
```

- [Engine manual](docs/slimpy.md): usage, embedding, implementation, benchmarks.
- [SLP-315 language standard](docs/standards/3_15.md): a single-file, versioned
  consolidation of the pinned Python 3.15.0 reference and core builtins, with
  Core, Host, and Extension profiles. Project draft, not an official PSF standard.
- [Upstream Cython baseline](docs/testing/cython.md): 7 passing and 11,432 failing
  discovered examples; 14 files need another adapter. Reproduce with
  `make upstream` followed by `make cython-report`.
- [Development instructions](AGENTS.md): architecture, naming, code taste, and
  requirements for honest upstream test evidence.

The engine currently supports functions, closures, basic control flow,
containers, host-loaded modules, reference counting, and cycle collection.
Classes, exception handling, async, arbitrary integers, and other required
language features remain to be implemented. See the manual for precise limits.
