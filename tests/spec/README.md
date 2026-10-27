# Language specification tests

A test262-style suite for the Python 3.15 language: one small, self-checking
script per topic, organized by the chapters of The Python Language Reference
and the built-in types, functions, and exceptions it relies on. Tests use no
standard library module, only `harness.py`, and assert behavior the
specification states.

Each file starts with a metadata comment block:

    # spec: reference/expressions.html#comparisons
    # description: Chained comparisons evaluate each operand once.

An optional `# negative: SyntaxError` line marks a test whose whole source
must fail to compile with that exception. Every other test passes by running
to completion.

Files a test needs, such as the modules and packages of the import tests, go
in a sibling directory named after it (`import_system.fixtures/` for
`import_system.py`); its contents are copied beside the test.

The `doctests/` chapter carries CPython's doctest-based tests (test_unpack,
test_unpack_ex, test_listcomps, test_genexps, test_generators, test_syntax,
test_extcall, test_metaclass) as spec tests. Each docstring is copied
verbatim, with a comment naming its source line, and checked by
`harness.run_doctests`, a core-only runner that parses examples exactly as
the doctest module does and supports the option directives these tests use.
Examples that relied on a library (collections, itertools, random, weakref,
warnings, test.support) were rewritten to use only the core language; each
rewrite is explained by a "(Ported ...)" note inside the docstring.

`tests/spec_runner.py ENGINE` stages each test beside `harness.py` and runs
it with the pinned CPython 3.15 oracle (which must pass, validating the test)
and with the engine. `make test-spec` runs it against ./spy.
