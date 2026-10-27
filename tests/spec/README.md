# Language specification tests

A test262-style suite for PLS-315, the Python Language Specification for 3.15
(`docs/standards/3_15.md`): one small, self-checking script per topic,
organized by chapter. Tests use no
standard library module, only `harness.py`, and assert behavior the
specification states.

Each file starts with a metadata comment block:

    # spec: PLS-315 13.10
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

The `ports/` chapter carries CPython's unittest-based language test modules
(test_augassign, test_binop, test_contains, ...), copied once from CPython
3.15.0 and run by `harness.unittest`, a core-only adaptation of the unittest
names they use (TestCase with its assertions, skips, subtests and fixtures, and
a subset of regular expressions for assertRaisesRegex). Each library import is
replaced by a core equivalent, and each change is marked "(Ported)". Modules
that test a library facility (test_userdict, for one) are not ported.
`harness.support` holds core versions of the test.support helpers they use.

The `programs/` chapter holds programs with the output CPython 3.15 gives them:
`harness.check_program` runs each with `print` and `input` bound in its own
namespace, and with its own copy of the built-in namespace, and compares what
it printed, followed by the last line of any escaping exception.

Tests name no library module. A host facility that PLS-315 leaves to the
implementation (the module cache, the lazy module set, the display hook, the
asynchronous generator hooks, and the texts *host*(f) by which messages name them) is reached through
`harness.host`, as test262 reaches its host through `$262`; an implementation
adapts the `Host` class to wherever it exposes them. `harness.qualified(cls)`
gives *tname* of an intrinsic type, its home module name and name, so a test
checks a message without assuming the module an implementation chose.

`tests/spec_runner.py ENGINE` stages each test beside `harness.py` and runs
it with the engine; `make test-spec` runs it against ./spy. With
`--oracle PYTHON` each test must also pass on that implementation, which
validates the test; `make test-spec-oracle` uses the pinned CPython 3.15 build.

The first line of every test, `# spec: PLS-315 X.Y[.Z], ...`, names the
clauses of `docs/standards/3_15.md` it exercises. `tests/spec_coverage.py`
(run by `make test-spec`) checks that each named clause exists and counts the
clauses of the normative chapters some test reaches; `--missing` lists the
rest. Every clause X.Y of chapters 6 to 29 and Annexes A and B has a test,
and the script fails when one does not.

The `grammar/` chapter checks the productions of Annex A by the sources they
accept and the sources they reject.
