# Cython upstream baseline

Engine: 0.4.0. This report measures the current
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
type/message and actual error filename/line are returned as structured JSON. A failed module initialization
fails its examples without executing them in an uninitialized namespace. Such
records carry `executed: false`; they are failures, not skips or passes. The
adapter does not bypass unsupported module code. Any unexpected driver stderr,
including sanitizer diagnostics, is a driver error.

Limitations are explicit:

- Runtime docstrings and `__test__` groups require `--dynamic` and successful
  oracle initialization. Static groups remain present if runtime discovery fails
  or produces a different group. Discovery errors fail the strict adapter.
- Unittest suites, `.pyx`, `.srctree`, compiled extension behavior, optimizer
  checks, and the C API/ABI are not adapted.
- The driver displays every non-`None` interactive expression, including inside
  loops and conditionals; function and class bodies use ordinary execution.
- Exception matching follows doctest type/message checks; traceback frames are
  not compared.
- Both current discovery runs use the pinned Python 3.15.0 oracle. A future-syntax discovery failure is
  adapter-ineligible, not a runtime pass or an engine syntax failure.
- Execution budgets and process timeouts prevent an unsupported test from
  hanging the reporting run. Such failures are recorded, never passed.

## Results

| Category | Count |
| --- | ---: |
| Selected `.py` files | 102 |
| Files with attempted static doctests | 89 |
| Adapter-ineligible files | 13 |
| Discovered examples | 11,450 |
| Passed examples | 383 |
| Failed examples | 11,067 |
| Upstream-directed skips | 0 |
| Driver errors/timeouts | 0 |

The additional dynamic-discovery run covers 11,543 examples in 90 files:
407 pass and 11,136 fail. Twelve files remain adapter-ineligible. Oracle module
initialization succeeds for 97 files and fails for four; one file cannot be
parsed by the oracle. Those failures are recorded independently of engine
outcomes. Reports are in `tests/results/cython-dynamic.json`.

Cython's unchanged `methodmangling_T5.py` passes all 48 static examples and all
24 additional examples in its formatted class docstring. Its dynamic selection
therefore passes 72 examples. This is a narrow language result, not a claim
about the compiled Cython variant or complete object-model compatibility.

The initial baseline was 7 passing and 11,432 failing examples. New passing
cases include argument binding, closures, class scopes, exception propagation,
context managers, generator functions, and slicing. Most remaining failures happen while initializing the
unchanged module; they are not independently diagnosed engine bugs. Passing
counts refer to examples, not complete test modules or Cython compiler tests.

Full records live in the generated `tests/results/cython.json`. The report is
not checked in because it embeds upstream test excerpts and is reproducible
from the pinned checkout. The generated file retains provenance for every
record. The 13 adapter-ineligible files are also named there.

## Reproduce

```sh
make upstream
make run-cython
make cython-report
make cython-dynamic-report
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
The adapter still needs unittest coverage and resolution of failed dynamic
discovery prerequisites. Extension loading and the CPython C API/ABI require their own profile
and upstream runner integration. No current report supports a claim of
near-complete Cython or Python compatibility.
