# CPython 3.15 test coverage

The engine is not Python 3.15 complete. No full-suite compatibility guarantee
has been established. This report records coverage without treating discovery,
skips, or unported cases as passes.

## Source and oracle

The source is CPython `v3.15.0`, commit
`d220409a13b77de7a6c30abe16ea90db01528edc`, pinned in
[`tests/upstream.json`](../../tests/upstream.json). The checkout retains its
upstream licenses. The oracle is compiled from that checkout in a separate
build directory. Neither CPython nor its libraries are linked into `spy`.

```sh
make oracle
make run-cython
make cpython-discover
make cpython-report
```

`make oracle` requires the platform's C development tools and the prerequisites
for building CPython. Missing optional CPython modules remain visible in its
configure/build output and in test discovery. The development oracle uses
CPython's normal dependencies; the engine still uses only C11 and libm.

## Complete file inventory and case discovery

[`tests/cpython.py`](../../tests/cpython.py) verifies the pinned revision and
rejects modifications to tracked upstream files. Every tracked file under
`Lib/test` is recorded with its SHA-256 hash, including fixtures and intentionally
invalid Python files. Static `test*` definitions are recorded as candidates.

Dynamic discovery uses CPython's own `findtests()` and `unittest.TestLoader`,
including `load_tests` hooks. Each module is loaded in a separate oracle process
with a timeout. Loader failures, diagnostics, skips, and case IDs are retained.
Four workers collect tests; this is not an interpreter performance benchmark.
Oracle parent and worker processes remove this repository's tests directory
from their import paths. This prevents local files such as `numbers.py` from
shadowing the pinned standard library. Upstream sources remain unchanged.

The first macOS arm64 discovery found:

| Item | Count |
| --- | ---: |
| Tracked files under `Lib/test` | 1,810 |
| Top-level test modules/packages | 557 |
| Discovered modules/packages | 472 |
| Oracle-skipped modules/packages | 85 |
| Discovered unittest cases | 56,761 |

These are discovery counts, not execution results or a complete cross-platform
case count. Skipped modules need discovery on applicable platforms. Generated
cases dependent on resources and build settings require further runs. Subtests
and dynamically generated assertions are not fully enumerated by unittest
loading. Static candidates cannot close these gaps. Whole-module execution
currently covers the nine modules listed below; the discovery ledger still
records the broader suite as unported.

The full ledger is written to `tests/results/cpython-discover.json`. It includes
unported cases and unresolved modules rather than excluding them from coverage.

## Doctest adaptation

The first language ports contain every doctest group found by CPython's
`DocTestFinder` in these files:

- `Lib/test/test_unpack.py`
- `Lib/test/test_unpack_ex.py`
- `Lib/test/test_listcomps.py`
- `Lib/test/test_genexps.py`
- `Lib/test/test_generators.py`
- `Lib/test/test_syntax.py`
- `Lib/test/test_extcall.py`
- `Lib/test/test_metaclass.py`

There are 1,435 examples. The latest local run passed 1,345 and failed 90, with
no skips or driver errors. All 1,435 passed on the pinned CPython oracle. These
counts cover only the eight listed files' doctest examples. The denominator
includes all 553 syntax examples and all 194 call examples, including diagnostics.

The adaptation replaces the doctest framework with the
existing persistent C driver, `run-cython`. Every example and expected result
is retained verbatim, including imports and exception diagnostics. A fresh
context is used for each doctest group, and examples run in order. The module
name is supplied as `__name__` so user-defined exception names can match.

The adapter does not initialize the entire upstream module in `spy`. Framework
imports and module fixtures execute in the oracle; their engine equivalents
remain unported. This adaptation therefore establishes example-level language
results, not full-module or standard-library compatibility. All unittest
classes in these files remain in the unported inventory.

Each group is also run by CPython's actual `DocTestRunner` with its original
module globals. Oracle failures make the strict port run fail. The engine uses
upstream doctest option flags and exception comparison rules. A skipped example
is recorded as skipped, never passed. Driver failures and timeouts are separate
from language mismatches. Later examples still run after a failed example, as
in doctest; a setup failure may therefore produce several downstream failures.

The latest report is `tests/results/cpython-doctests.json`. It records source
locations, inputs, expectations, actual outputs, per-file totals, oracle results,
engine source hashes, driver hash, platform, and interpreter version. Reports are
generated artifacts and are ignored by Git.

```sh
make test-cpython-doctests  # strict: every selected example must pass
make test-cpython          # also requires closing the full coverage inventory
```

Both strict targets currently fail. `cpython-report` and `cpython-discover`
return success when they successfully write a report; that status does not mean
the reported tests passed. The discovery gate remains failing while unittest
ports, skipped platforms, and dynamic-case coverage are unresolved.

## Whole-module unittest adaptation

Nine complete unchanged upstream modules run in the engine. All 154 discovered
cases pass with both the adapted framework and CPython's original framework:

| Module | Cases |
| --- | ---: |
| `test_decorators` | 16 |
| `test_augassign` | 7 |
| `test_int_literal` | 6 |
| `test_unary` | 6 |
| `test_keywordonlyarg` | 11 |
| `test_named_expressions` | 74 |
| `test_longexp` | 1 |
| `test_unicode_identifiers` | 3 |
| `test_exception_variations` | 30 |

The assignment-expression module also executes 99 subtests. Their results and
parameters are recorded. The runner compares the sequence of subtest statuses
with CPython's execution; a missing subtest prevents a case from passing.
The large-expression test compiles and evaluates a 65,580-element list literal.

```sh
make test-cpython-unittest
make cpython-unittest-report
```

The only replacement is the test framework: imports of `unittest` load
[`tests/support/unittest.py`](../../tests/support/unittest.py) through the test
driver's source-loader callback. This module is never installed or embedded in
the engine. Subsequent module search uses the unchanged pinned `Lib` directory,
including the invalid-source fixture imported by the Unicode identifier test.
An earlier plain module takes precedence over a later package. No upstream imports, definitions, decorators, assertions, or test
bodies are removed. The runner retains every discovered case ID and records
module/class/test setup, teardown, and cleanups. Failed setup leaves dependent
cases recorded as unexecuted failures, and skips remain separate from passes.

The replacement framework currently implements the assertions and fixtures
needed by these nine modules, including subtests that continue after failure.
Exception-message patterns support literal characters and the `?` quantifier;
other regex syntax fails explicitly. The adapter's matching is checked against
256 host-regex examples, including negative matches. It is not a complete
unittest implementation: warning assertions, full regex support, expected-failure
handling, and continuation after cleanup failures remain gaps. Unsupported framework operations fail
explicitly. Dynamically located or imported test classes are recorded as
adapter-ineligible rather than silently omitted. Extending the selection
requires resolving those obligations.

`tests/results/cpython-unittest.json` records oracle results, cases, fixtures,
actual errors/output, and hashes of the engine, driver, framework, and upstream
files. Passing this selection does not close the complete-suite coverage gate.

The complete object-module attempt in `tests/results/cpython-objects.json`
accounts for 635 cases: 143 from `test_dict`, 30 from `test_hash`, 37 from
`test_raise`, 36 from `test_funcattrs`, 17 from `test_subclassinit`, 40 from
`test_super`, and 332 from `test_bytes`. All remain unexecuted failures:
their unchanged initialization reaches unsupported syntax or the unavailable
`time`, `sys`, or `array` modules. Actual error filenames and line numbers are
retained so failures in imported dependencies can be distinguished from the
top-level test module. For example, `collections` uses the still-unsupported
Python 3.15 `lazy from ... import ...` syntax. The report records each actual failure. Supplementary
construction, inheritance, hash, and dictionary checks do not count as passing
these cases. The class-construction work follows the original `test_subclassinit`
and `test_super` cases; it does not remove their imports to claim module success.

The complete `test_unicode_identifiers` module now passes, including its
unchanged imported invalid-source fixture and checks of the error location.
Independent oracle checks cover all 1,114,112 identifier code points and
297,124 source/normalization cases. Syntax-error messages and spans outside
the tested cases remain incomplete.

A separate whole-module attempt of `test.test_coroutines` and
`test.test_asyncgen` accounts for 185 oracle-discovered cases. All 185 currently
fail before their bodies execute because unchanged module initialization needs
unavailable `ast` and `inspect` modules. The report is
`tests/results/cpython-async.json`; local async
semantic checks are not counted as passing these upstream cases. Reproduce:

```sh
tests/upstream/cpython-build/python.exe tests/cpython.py unittest \
    --module test.test_coroutines --module test.test_asyncgen \
    --report tests/results/cpython-async.json --report-only
```

The complete `test_range` module has also been attempted: its 29 cases remain
unexecuted failures because module initialization requires `sys`. The
`test_exception_variations` module now passes all 30 cases, including `except*`,
and is included in the strict selection.

The complete `test_list` and `test_sort` modules account for another 90 cases.
Their initialization fails on missing `signal` and `test` imports respectively;
all 90 are recorded as unexecuted failures in `tests/results/cpython-lists.json`.
The local list-method and sorting checks do not count as passing these modules.

The template-string attempt covers all 17 cases in `test.test_tstring`, all
13 in `test.test_string.test_templatelib`, and all 37 in `test.test_raise`.
All 67 pass in the isolated oracle. All 67 remain unexecuted engine failures:
module initialization needs `errno`, `sys`, and `_ast`, respectively. The
template syntax in `annotationlib` now parses; its next dependency failure is
retained in the report. Reproduce:

```sh
tests/upstream/cpython-build/python.exe tests/cpython.py unittest \
    --module test.test_tstring --module test.test_string.test_templatelib \
    --module test.test_raise --report tests/results/cpython-templates.json \
    --report-only
make test-templates
```

The supplementary template test reads all 21 source/diagnostic pairs directly
from the unchanged upstream `test_syntax_errors` table. It also compares 336
valid literals, constructors, concatenation, iteration, matching, conversions,
and suspended expressions against the oracle. This is a table port and local
semantic coverage, not a substitute for those 67 whole-module cases.

## Implementation work driven by these tests

The ports drove unpacking and chained assignment, iterator consumption,
comprehension scopes, Python 3.15 starred comprehensions, lazy generator
expressions, generator functions, `send`/`throw`/`close`, `yield from`,
suspension through exception handlers and cleanup, slices, positional and
keyword argument binding, basic classes and bound
methods, global/nonlocal declarations, private-name mangling, decorators,
and exception propagation. The keyword-only tests drove writable positional and
keyword defaults, sorting options, interactive compilation, and function argument
metadata. Assignment-expression tests drove parentheses restrictions, comprehension
rebinding diagnostics, and private-name diagnostics. Call doctests drove keyword
validation order and complete missing-argument diagnostics. All 46 doctest examples from `test_unpack`
pass. This does not include that file's unittest corner cases.

The 24 generator tutorial examples, all 20 list-comprehension examples, and
all 73 metaclass examples pass. The metaclass examples drove custom namespace
mappings, callable `__prepare__` hooks, class metadata, custom MROs, and class
keyword diagnostics. Supplementary comparisons exercise mapping callback order,
exceptions, dictionary-subclass globals, and explicit `type.mro` independently
of the installed custom MRO.
The generator tuple-address-reuse example uses a bounded per-context cache of
released small-tuple storage. Cached allocations retain no element references.
Remaining failures include module fixtures, library imports, runtime
introspection, finalization, and diagnostics. Generator unittest cases, including
`test_yield_from.py`, remain unported; inspecting those cases is not a passing
result. The [manual](../slimpy.md) records the broader
language gaps. The [versioned standard](../standards/3_15.md) remains the full
target; its requirements have not been reduced to the implemented subset.

## Supplemental method checks

`tests/generator_metadata.py` runs the unchanged body of
`test_generators.GeneratorTest.test_name` under its original class name, with
the local unittest adapter, and validates it against the pinned interpreter.
`tests/frozendict.py` similarly runs eight methods from
`test_dict.FrozenDictTests`, the frozen eval/exec methods from
`test_builtin.BuiltinTest`, and `test_builtin.TestType.test_type_frozendict`.
These methods do not use module fixtures or the original classes' mixins.
Their source bodies and assertions are preserved; surrounding imports and
unrelated methods are not transplanted.

These checks are supplemental selections, not whole-module passes, and are
not added to the 154-case whole-module result. Pickling tests, CPython-only
checks, and all other cases stay in the full test inventory. Additional oracle
comparisons cover suspended-object lifecycle states, frozen mapping protocols,
subclass identity, hash callbacks, and immutable execution namespaces.
