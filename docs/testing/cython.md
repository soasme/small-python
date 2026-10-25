# Cython upstream baseline

Date: 2026-10-25. Engine: 0.1.0 development. This report measures the current
partial engine; it is not a full Cython-suite compatibility claim.

## Sources inspected

Cython repository: <https://github.com/cython/cython>  
Commit: `a76568d4e9cce24843e5b9e41f67e4dd5d8a6773`  
Upstream version reported by `runtests.py`: 3.3.0.

The checkout is downloaded under `tests/upstream/cython`. The inspected runner
is `runtests.py`, particularly `TestBuilder.handle_directory`,
`CythonRunTestCase.run_doctests`, and `PureDoctestTestCase.run`.
It selects tests using modes/tags, compiles `.py`/`.pyx` files into extensions,
loads compiled modules for doctests, additionally runs eligible `.py` files
under host Python, and supports unittest and multi-file build cases.

## Inventory

Counts below are source files, not test case counts:

| Directory | `.py` | `.pyx` | `.srctree` | Purpose |
| --- | ---: | ---: | ---: | --- |
| `run` | 102 | 807 | 95 | Execution, doctests, unit tests, extension behavior |
| `compile` | 6 | 197 | 12 | Successful compilation |
| `errors` | 12 | 253 | 0 | Expected compiler diagnostics |
| `build` | 0 | 1 | 36 | Multi-file build behavior |
| `memoryview` | 1 | 22 | 6 | Memoryview and buffer-related behavior |
| `buffers` | 0 | 4 | 0 | Buffer protocols |
| `pyximport` | 0 | 0 | 7 | Import-time compilation |
| `wrappers` | 0 | 3 | 0 | Wrapper generation |
| `broken` | 0 | 51 | 0 | Upstream known-broken cases |

The JSON report also inventories headers, `.pxd`, `.pxi`, C++, and other support
files. Compiler diagnostics and C declarations are not Python source semantics;
they cannot be counted as language tests simply by feeding them to `spy`.

## Adapter contract

`tests/run_cython.py` discovers static docstrings in every selected `.py` file
under `tests/run`. It uses Python's `doctest` parser and expected-output matcher.
It sends the complete, unchanged source module to `run-cython`, then sends the
upstream examples in order. Each docstring group gets a fresh context. Examples
in a group share state, including state preceding an expected exception.

The transport decodes source using its declared encoding and supplies UTF-8
text to the embedding API. It changes no function bodies, imports, decorators,
expected outputs, assertions, or example inputs. Engine output and error
type/message are returned as structured JSON. A failed module initialization
fails its examples; the adapter does not bypass unsupported module code.

Limitations are explicit:

- Dynamic `__test__` generation, unittest suites, `.pyx`, `.srctree`, compiled
  extension behavior, optimizer checks, and the C API/ABI are not adapted.
- The driver displays the final top-level expression of an example. An example
  containing multiple interactive expressions needs a fuller display adapter.
- Exception matching follows doctest type/message checks; traceback frames are
  not compared.
- The discovery host was Python 3.14.3. A future-syntax discovery failure is
  adapter-ineligible, not a runtime pass or an engine syntax failure.
- Execution budgets and process timeouts prevent an unsupported test from
  hanging the reporting run. Such failures are recorded, never passed.

## Results

| Category | Count |
| --- | ---: |
| Selected `.py` files | 102 |
| Files with attempted static doctests | 88 |
| Adapter-ineligible files | 14 |
| Discovered examples | 11,439 |
| Passed examples | 7 |
| Failed examples | 11,432 |
| Upstream-directed skips | 0 |
| Driver errors/timeouts | 0 |

Six passing examples are from `tests/run/boolop_py.py`; one is from
`tests/run/file_encoding_T740.py`. The failing-example error categories were
11,419 `SyntaxError`, 10 `NameError`, 2 `OverflowError`, and 1
`ModuleNotFoundError`. Most errors happened while initializing the unchanged
module, so these counts are **not** 11,432 independently diagnosed engine bugs.

Full records live in the generated `tests/results/cython.json`. The report is
not checked in because it embeds upstream test excerpts and is reproducible
from the pinned checkout. The generated file retains provenance for every
record. The 14 adapter-ineligible files are also named there.

## Reproduce

```sh
make upstream
make run-cython
make cython-report
```

`make test-cython` runs the same selection and exits nonzero for failures or
adapter-ineligible files. `make cython-report` explicitly uses report-only mode;
its successful command exit means the report was produced, not that tests passed.
Both fail if the checkout, driver, or selected tests are missing.

A narrow upstream smoke check is useful during development, but must keep its
selection visible:

```sh
python3 tests/run_cython.py --select boolop_py.py --report tests/results/cython-boolop.json
```

The official Cython runner was also executed, unchanged, as a host control:

```sh
cd tests/upstream/cython
uv run --no-project --python /opt/homebrew/bin/python3 --with setuptools==80.9.0 python runtests.py -3 --no-unit --no-doctest --no-cpp --work-dir /tmp/spy-cython-py3-baseline boolop_py
```

It reported 4 passing runner tests, including compilation and pure-Python
execution, on CPython 3.14.3 with Cython language level 3. The compiler produced
and loaded `boolop_py.cpython-314-darwin.so`. Replace the explicit interpreter
path with the intended local Python when reproducing this control. `setuptools`
is an isolated development dependency, not an engine dependency. This control
verifies the selected fixture in Cython's own harness; it is neither a full
Python 3.15 result nor a result for `spy`.

## Next conformance work

The first priority is semantic implementation, not adjusting test expectations:
full function signatures, unpacking, class definitions and protocols,
exceptions, Unicode, arbitrary integers, comprehensions, and generators.
The adapter then needs unittest, dynamic doctest, and interactive-display
coverage. Extension loading and the CPython C API/ABI require their own profile
and upstream runner integration. No current report supports a claim of
near-complete Cython or Python compatibility.
