# Moving calls onto the machine: handoff

State at commit 158c94ed (2026-11-22). This note is for whoever continues
the work of running every call Python code makes on the instruction
machine, so that the C stack depth does not grow with Python call depth
and a run can pause at any step (see `AGENTS.md` and `docs/metering.md`
section 3.8).

## 1 The goal and how it is measured

A Python-to-Python call pushes a heap frame on the running machine. A
*nested activation* is any place where C code calls back into the
evaluator instead: `run_machine` entered while another machine is already
running in the same context (`c->machines > 0`). Each such site grows the
C stack per Python level and stops a pause from taking effect until the C
code returns.

The measurement is the **census**: every spec test in `tests/spec` runs on
a pausing probe build, which records the C backtrace each time a nested
activation begins (appendix A). A *chain* is one distinct backtrace and
source line. The goal is zero chains on every spec test, with no long-tail
exceptions.

| Date | Chains | Note |
| --- | --- | --- |
| 2026-11-19 | 703 | first full census of the second batch |
| 2026-11-20 | 395 | after the nest-worktree batch |
| 2026-11-21 | 270 | |
| 2026-11-22 | **35, in 3 of 1039 tests** | at 158c94ed; the probe build passes all 1039 spec tests |

## 2 What remains in the census

All 35 chains, grouped by the first C function that calls back:

| Family | Chains | Entry | Source (spec test, line) | What runs in C |
| --- | --- | --- | --- | --- |
| `dict.fromkeys` of a dict subclass or of a class with its own `__setitem__`/`__eq__` | 19 | `dict_fromkeys` → `type_call`, `set_index` → `call_pair`, `map_set_hash` → `map_find_compare` | ports/test_dict 412-467, 1371-1393, 2080-2101 | the class call that makes the result, its `__setitem__`, and key `__eq__` |
| `dict.update` called as a method (`d.update(x)`) of a mapping or iterable instance | 11 | `call_method` → `dict_update` → `extend_container` (`get_iterator`, `iterator_next`, `get_index`, `keys_iterator`) | ports/test_dict 239-296 | `keys()`, `__iter__`, `__next__`, `__getitem__` of the argument |
| a dict method's key lookup | 2 | `call_native_method` → `method_call` → `map_find_hash` → `map_find_compare` | ports/test_dict 1676-1677 (`d.get(key)`) | the stored key's Python `__eq__` |
| `format()` of a value with a Python `__format__`, nested | 1 | `builtin` → `stringify` → `format_object` → `format_value` | ports/test_dict 1371 | the inner `__format__` |
| a lazy submodule loaded by an attribute read | 2 | `attribute_step` → `attribute_lookup` → `attribute_value` → `lazy_submodule` → `import_module` → `execute_module` | imports/import_system, imports/lazy_dotted_hook | the submodule's body |

Each family already has a machine form for a neighbouring case, to reuse
rather than duplicate:

- `|=` of a dict with a mapping or iterable instance runs on the machine
  (Changelog, 0.10.0); `dict.update` as a method should take the same
  path instead of `extend_container`.
- Comparisons on the machine go through `comparek` (and `equalk`); a
  call step with arguments goes through `step_callk`; `callk` takes a
  continuation (`k_state`/`k_resume` carry its state).
- Imports run module bodies on the machine through `importk` and
  `module_loadk`; `lazy_submodule` still calls `import_module`.
- `format()` fields already read attributes and indices on the machine
  (`82341d5f`); the nested `__format__` call is the leftover.

## 3 What the census does not see

The census is a lower bound. These still run Python from C, either by
design or because no spec test reaches them on the probe:

- **Reads in C.** There is no tree walker: every body, interactive and
  expression units included, runs on the machine. Two reads still run in
  C: a match pattern's dotted value (`pattern_value`), whose attribute
  getter is called from C, and the names of a store target of names or
  literals (`store_name`), which a globals mapping's `__getitem__`
  answers from C.
- **By design.** A host function's `spy_call` (its `spy_callk` runs on the
  machine); trace and profile functions (`sys.settrace`, `sys.setprofile`),
  which `comparek` and the call paths call in C; the once-per-context load
  of the embedded intrinsics module.
- **Known nesting not in a spec test:**
  - `throws_in` declines a `yield from` whose delegate is not a plain
    Python generator (builtin-subclass delegate, builtin method,
    staticmethod `close`/`throw`), so `g.throw()` and `g.close()` run the
    whole throw in C (`generator_send_args`).
  - `filter()` whose predicate returns an instance with a Python
    `__bool__` (`filter_returned` → `truthy`), and the same for
    `map_filter_conversion_calls` and `sentinel_compared`.
  - `map(dict.__getitem__, ...)` with `__missing__`, and
    `map(P.x.__get__, ...)` (`map_convert` makes a call step only for
    `map_steps` natives).
- **Stale text.** `docs/metering.md` section 3.8 still lists as nesting
  sites that the census no longer shows in any spec test (augmented
  `__setitem__`, unpacking `__iter__`, strict `zip`/`map`, `in` searches,
  the metaclass call, imports, `exec` and `eval`). Rewrite it from the
  census once it reaches zero.

To widen the census, add spec tests for these forms (each must pass on the
pinned CPython oracle), then fix what they show.

## 4 Open problems

- **CI coverage is red.** `make coverage` reports `spy.c` 42347/43099
  lines; 752 lines no test runs (GitHub run 44890114952). `AGENTS.md`
  requires every line to run; cover each with a spec test where the
  standard states the behaviour, through `tests/api` or `tests/oom`
  otherwise, or delete code no input can reach. Run coverage in a scratch
  clone, never the working tree: it rebuilds with profiling flags.
- **A metaclass `__prepare__` made by a descriptor, under pausing.** On the
  pause runner (`run-spec` plus `spy_set_limit(c, SPY_LIMIT_PAUSE, 1)`):

  ```python
  class Gives:
      def __get__(self, instance, owner):
          return lambda name, bases, **kw: {}
  class M(type):
      __prepare__ = Gives()
  class Z(metaclass=M): pass
  ```

  raises `TypeError: 'object' object is not subscriptable` at the class
  statement and aborts; a longer script segfaults. It also fails before
  this batch (5cc2ed3). A function that already exists (a module-level
  `def`) works; a fresh one, owned only by the getter's result, fails, so
  it is a reference released too early on the `prepare_read` →
  `class_part` → `class_prepare` → `class_prepared` path. macOS guard
  malloc (`DYLD_INSERT_LIBRARIES=/usr/lib/libgmalloc.dylib`) reports a free
  of memory that was never allocated. The plain runner is unaffected.
- **gcc warning.** `gcc -O1` (the sanitize build) warns that `value` may
  be used uninitialized in `run_steps`; `-O2 -Werror` builds are clean.
- **Owed for this batch:** a performance A/B of the batch head against the
  last measured baseline (alternate the programs over rounds, average wall
  time over several code layouts, and report before → after), and ASan in a
  Linux container (AddressSanitizer hangs at startup on the macOS dev
  machine).
- **Conformance gaps found on the way, not yet fixed:**
  - `super.__new__(super)` raises "super(): no arguments" (CPython makes
    an empty super); `mysuper(F).__get__(obj, F)` called explicitly returns
    a plain `super`, not the subclass.
  - No `DeprecationWarning` for the `(type, value, tb)` forms of
    `throw()` and `athrow()`; check the standard's position first.
  - `list()` of a builtin-iterator subclass instance never calls the
    inherited `__length_hint__`.
  - Builtin adapters (`zip`, `enumerate`, `map`, `filter`) do not pass on
    the `StopIteration` value of the generator they end on.
  - A trace function sees a `line` event for a function's docstring, and
    under `-OO` for a class's removed docstring; CPython reports neither.
    A function body compiles its docstring as an expression statement, and
    `-OO` turns a removed docstring into `pass`. Without `-OO` both report
    a class's docstring, which stores `__doc__`.

## 5 How each fix is made

Every commit of this work carries:

1. the fix in `spy.c`, reusing `callk`, `comparek`, `step_callk` or
   `attribute_callk` rather than a new continuation shape;
2. a spec test in `tests/spec` (test262-style: small, self-checking, its
   header naming the clauses) that passes on run-spec, on the pause runner
   and on the pinned CPython oracle (`spec_runner.py --oracle`), and whose
   chains are zero on the probe; check the name is free before writing it;
3. a TLA+ model case for the behaviour (`tests/tla/*.tla` and its
   `.replay.py`), passing `tests/tla_check.py` on run-spec and the oracle;
   a new standard clause also needs an entry in `tests/tla/coverage.txt`;
4. a Changelog line under `Unreleased`, saying what changed for a user;
5. a commit message ending with the results: spec counts on run-spec and
   the pause runner, spec coverage, `make test-tla`, and the chain count of
   the tests it touches.

Never weaken the standard to make a test pass. When the oracle and spy
fail the same way, the test or the standard is wrong.

## 6 Before pushing

The last push found four bugs that per-commit checks missed. Run all of
these:

- `make test` (it includes `tests/api`, which exercises tracing,
  interactive units and limits that the spec suite does not);
- `gcc -O2 -std=c11 -Wall -Wextra -Wpedantic -Werror -c` of `spy.c`,
  `spy-std.c`, `cli.c`, `spy-worker.c` and `spyc/_spyc.c` in a Linux
  container (clang misses gcc-only warnings);
- the clang test job locally: `tools/run_workflow.py test.yml -j test
  --matrix os:ubuntu-latest --matrix compiler:clang`, run from a plain
  `git clone` of the branch (a worktree makes `check-api` fail);
- the sanitizers: `make CC=gcc sanitize` in a Linux container, from a git
  clone with its tags. Without Python 3.15 in the container it stops at
  `tests/files.py`; the spec and API runs before that point still count.

What they caught, as patterns to look for in new code:

- a step that finishes inline must not leave values run_steps releases
  again at the end of its case (BC_DECORATE);
- C code that runs Python (a trace function) between setting `c->k_*` and
  reading them lets the inner run take the pending call: take and clear
  them first (`k_enter`);
- moving a path onto the machine must keep the walker's version
  (interactive `except*` lost its group split);
- a zero-length `memcpy` from a NULL `argv` is undefined behaviour: guard
  it with `if (argc)`.

## Appendix A: the census probe

The probe is `tests/run-spec.c` with `spy_set_limit(c, SPY_LIMIT_PAUSE, 1)`
before the module is created, linked with a `spy.c` patched in two places:
`run_machine` made `noinline`, and `if (c->machines) probe_nested(c);` placed
before `c->machines++` in it. `probe_nested` writes each new backtrace once
to the file `SPY_PROBE` names:

```c
#include <execinfo.h>
#include <mach-o/dyld.h>
static FILE *probe_file;
static void probe_nested(SPYContext *c) {
    static int init; if (!init) { init = 1; const char *p = getenv("SPY_PROBE"); if (p) probe_file = fopen(p, "a"); }
    if (!probe_file) return;
    void *a[24]; int n = backtrace(a, 24);
    static unsigned long seen[65536];
    unsigned long h = 1469598103934665603ul; intptr_t slide = _dyld_get_image_vmaddr_slide(0);
    for (int i = 1; i < n; i++) h = (h ^ (unsigned long)((intptr_t)a[i] - slide)) * 1099511628211ul;
    size_t line = c->frame_line ? *c->frame_line : c->line;
    h = (h ^ line) * 1099511628211ul;
    unsigned long *slot = &seen[h & 65535]; if (*slot == h) return; *slot = h;
    fprintf(probe_file, "L%zu ", line);
    for (int i = 1; i < n; i++) fprintf(probe_file, "%lx ", (unsigned long)((intptr_t)a[i] - slide));
    fputc('\n', probe_file); fflush(probe_file);
}
```

Build it with `cc -O1 -g -fno-omit-frame-pointer -std=c11
-D_DARWIN_C_SOURCE` (macOS). Run each spec test as `spec_runner.py` does:
`harness.py` and the test, renamed `test_spec.py`, in a fresh directory,
together with the contents of its `NAME.fixtures/` directory if it has
one. Symbolize the addresses with `atos -o probe -l 0x100000000`, dropping
the generic call frames (`call`, `call_function`, `spy_call`,
`rich_compare` and the like) to see the first specific C site.

Two checks before trusting a census:

- run the whole spec suite on the probe binary; a test that crashes
  leaves no chains and looks fixed;
- symbolize with the probe built from the tree the census ran on, never
  one rebuilt later.
