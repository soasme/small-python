# Small Python

Version 0.9.0

## Table of Contents

- [1 Introduction](#1-introduction)
  - [1.1 Main features](#11-main-features)
  - [1.2 Project goals](#12-project-goals)
- [2 Usage](#2-usage)
  - [2.1 Installation](#21-installation)
  - [2.2 Quick start](#22-quick-start)
  - [2.3 Command-line options](#23-command-line-options)
  - [2.4 Local tests](#24-local-tests)
  - [2.5 Upstream Cython tests](#25-upstream-cython-tests)
  - [2.6 Benchmarks](#26-benchmarks)
- [3 Specifications](#3-specifications)
  - [3.1 Python language support](#31-python-language-support)
  - [3.2 Modules](#32-modules)
  - [3.3 Standard library and host services](#33-standard-library-and-host-services)
  - [3.4 C API](#34-c-api)
  - [3.5 Python binding](#35-python-binding)
  - [3.6 Rust crates](#36-rust-crates)
  - [3.7 Go module](#37-go-module)
  - [3.8 Java artifacts](#38-java-artifacts)
- [4 Internals](#4-internals)
  - [4.1 Source representation](#41-source-representation)
  - [4.2 Executable generation](#42-executable-generation)
  - [4.3 Runtime values](#43-runtime-values)
  - [4.4 Garbage collection](#44-garbage-collection)
  - [4.5 Calls and scopes](#45-calls-and-scopes)
  - [4.6 Repository and toolchain](#46-repository-and-toolchain)
- [5 Sources and licenses](#5-sources-and-licenses)

## 1 Introduction

Small Python is a small, embeddable Python-language engine written in C11. The command
is `spy`, the standalone-program generator is `spyc`, and the embedding API uses
the `spy_*` prefix. The core consists of `spy.c` and `spy.h` and depends only on
the C runtime and math library. It does not link or invoke CPython.

The language target is [PLS-315:2026-draft2](standards/3_15.md), the project's
versioned specification of the Python 3.15 core language. The engine conforms
to its Core profile, as [3.1](#31-python-language-support) states with its
evidence. It does not claim the standard library, CPython's C API, or a passing
upstream Cython suite.

### 1.1 Main features

- One core C implementation file and one public embedding header.
- Independent runtime contexts with explicit ownership of values.
- Functions with argument binding and closures, basic classes and exceptions,
  iterators, comprehensions, generator functions and delegation, sequence slices,
  and host-loaded modules.
- Reference counting with iterative destruction and explicit cycle collection.
- A command-line interpreter and a basic interactive shell.
- Native modules: shared libraries that a program imports without
  rebuilding its host.
- C source generation for programs that run without a Python installation or
  the original Python source file.
- Local semantic checks, a pinned CPython oracle and test inventory, and adapters
  that run upstream CPython and Cython doctest examples and report failures.

### 1.2 Project goals

The intended engine supports the complete 3.15 language, including classes,
exceptions, modules, generators, and async semantics, without requiring the
standard library. Further goals are a Python-written shell with contextual
colorization, optional C library wrappers, near-complete applicable upstream
test coverage, small executables, and a lifecycle below 300 microseconds.

These are goals. There is no current claim of a few-kilobyte full Python engine,
near-100% test coverage, Cython extension compatibility, or complete language
support. A release's tests and measurements must substantiate each claim.

## 2 Usage

### 2.1 Installation

A Makefile builds the engine and tools on a host with a C11 compiler, an archive
tool, and the platform C/math libraries:

```sh
make
```

The outputs are `bin/spy`, `bin/spyc`, and `libspy.a`. No Python installation is
needed to build or run those three artifacts. spyc is a Python program built
by the previous release's spyc, which `make` downloads once and checks against
its checksum (`SPYC_BOOTSTRAP=path/to/spyc` names another; [Building
programs](build.md) 9.1). Python is a development dependency for test adapters
and documentation tools.

Build options are set at the top of the Makefile or on the command line:

```sh
make clean
make CC=clang CONFIG_WERROR=y
make clean
make CONFIG_LTO=y
make clean
make CC=clang CONFIG_PGO=y
```

Clean before changing compiler or instrumentation flags. The source language
remains C11; LTO is an optional compiler/linker optimization, not a dependency.
`CONFIG_PGO=y` is clang's profile-guided optimization: it first builds an
instrumented copy of the engine under `.obj/pgo`, runs the specification tests
on it, merges the profile with `llvm-profdata` (set `LLVM_PROFDATA`, for
example to `xcrun llvm-profdata` on macOS), and compiles `spy.c` with it. The
profile comes from the specification tests, never from `bench/programs`.

An optional installation uses the conventional `PREFIX` and `DESTDIR` variables:

```sh
make install PREFIX=/usr/local
make install PREFIX=/usr/local DESTDIR=/tmp/smallpython-package
```

Installation places commands in `bin`, the header in `include`, the archive in
`lib`, and this manual in `share/doc/smallpython`. Installing is not required to use
the engine from its build directory.

### 2.2 Quick start

Execute a source file or command:

```sh
bin/spy examples/hello.py
bin/spy -c 'print(sum(range(10)))'
```

Generate and compile a standalone program:

```sh
bin/spyc -o hello examples/hello.py
./hello
```

`spyc` generates C and compiles it with the compiler spyc itself was built
with; `spyc -e -o hello.c` writes that file instead, for any compiler:

```sh
bin/spyc -e -o hello.c examples/hello.py
cc -std=c11 -Os -I. hello.c spy.c -lm -o hello
```

The executable embeds its source and interpreter. It requires neither a Python
installation nor the original `.py` file. It still uses the platform C/math
libraries. Static linking depends on the target platform.

### 2.3 Command-line options

#### 2.3.1 `spy` interpreter

```text
usage: spy [--mount dir]... [-O | -OO] [-c source | file.py | -] [arg]...
       spy [--mount dir]... [-O | -OO] (-i | --version)
```

| Option | Effect |
| --- | --- |
| `--mount dir` | Let `open` reach `dir` at its own resolved path; repeatable, and replaces the default mount of the current directory |
| `-O`, `-OO` | Set the optimization level to 1 (no `assert`, `__debug__` is `False`) or 2 (no docstrings either), as Python's options do |
| `-c source` | Execute the supplied text |
| `-i` | Start the interactive shell |
| `--version` | Print the engine version |
| `file.py` | Execute a source file |
| `-` or no arguments | Read a complete program from stdin |
| `arg` | An argument of the program, which follows it into `sys.argv` |

`sys.argv` is set as Python sets it:

| Run | `sys.argv` |
| --- | --- |
| `spy file.py arg...` | `['file.py', arg...]` |
| `spy -c source arg...` | `['-c', arg...]` |
| `spy - arg...` | `['-', arg...]` |
| `spy` (stdin) or the shell | `['']` |

`sys.orig_argv` is the whole command line, `spy` and its options included.
`-m` and the other CPython switches are not implemented.

The interactive shell keeps global variables between submissions, and a blank
line ends a compound statement. It is a small C input loop: multiline
editing, contextual colorization, completion, and a Python-written shell are
not implemented yet.

#### 2.3.2 `spyc` program generator

```text
usage: spyc [build] [options] [-o program] (input.py | -m module) [module.c | libmodule.a]... [-- cc-arguments]
       spyc [build] -e [options] [-o program.c] (input.py | -m module) [module.c | libmodule.a]...
       spyc [build] -c [options] [-o modules.c] (input.py | -m module)...
       spyc run [options] [module.c | libmodule.a]... (input.py | -m module) [argument]...
       spyc test [options] [module.c | libmodule.a]... [test.py | directory]...
       spyc clean
       spyc version
```

`spyc` bundles a program and the modules it imports into one C translation
unit. It finds each import as CPython's path finder would, over the entry's
directory and each `-I` root, embeds the sources, and serves them through a
generated `SPYModuleLoader`. A missing import fails the build, unless the
program guards it with `try`/`except ImportError`. spyc produces no native
code or bytecode for Python functions.

| Command | Effect |
| --- | --- |
| `spyc` or `spyc build` | Build a program |
| `spyc run` | Build into the cache `__pycache__/spyc` of the working directory, then run the program with the arguments after the entry. It compiles again only when a source, a C module, a header, or a library changed |
| `spyc test` | Run each `test_*.py` below the paths that way; count those that exit with 0 |
| `spyc clean` | Remove the cache |
| `spyc version` | Print the version |

Outputs:

| Option | Output |
| --- | --- |
| (none) | An executable (`a.out` without `-o`) |
| `-e` | The C file of that executable (`out.c` without `-o`) |
| `-c` | A C file for a host with its own `main`: each entry's source as `const char spy_name[]` (`game.py` gives `spy_game`) and the loader `spy_name_load` |

For an executable, spyc compiles a C file with a `main` that runs the entry.
It uses the compiler and link flags of its own build, against the `spy.h` and
libraries beside it or under the installation prefix; `-v` prints that
command. The program mounts its working directory and has its command line
as `sys.argv`. On Windows spyc writes C only (`-e` or `-c`). A failed or
interrupted build removes the files it began to write.

What goes into the program is found from its imports. In each search root,
`import NAME` takes, in order:

| Found | Becomes |
| --- | --- |
| `NAME/__init__.py` | A package, embedded |
| `NAME.c` | A C module exporting `spy_init_NAME`, compiled in and registered as `NAME` |
| `libNAME.a` | An archive with a member exporting `spy_init_NAME`, linked in and registered as `NAME`, whatever language built it |
| `NAME.py` | A module, embedded |

A standard module (`sys`) is registered and links the standard layer
(`spy-std.c`). Only what imports cannot show is named:

| Input | Effect |
| --- | --- |
| `-x MODULE` | Leave the module to the host |
| `-D MODULE` | Add a module that only dynamic imports name |
| `-I DIR` | Search another root after the entry's directory |
| `NAME.c`, `libNAME.a` | A C module outside the roots |
| `-- ARGS` | Arguments for the compiler |

So `spyc -o pong pong.py -- -lraylib` builds
[`examples/pong`](../examples/pong) in one step, and
[`examples/jsonify`](../examples/jsonify) writes its `json` module in Rust.
`-O`, `-OO`, `--minify`, `--metafile`, `--deps`, `--analyze`, and `-v`
complete the options. [Building programs](build.md) is the full reference.

### 2.4 Local tests

```sh
make test
make sanitize
```

#### 2.4.1 `make test`

`make test` builds everything, then runs:

- the C API tests: ownership, context isolation, error recovery, reference
  cycles, deep graph destruction, and an execution budget;
- the allocation-failure tests (`tests/oom`);
- the thread tests (`tests/threads`): a context on each of four threads at
  once, sharing nothing;
- the host file and standalone-executable checks;
- the language specification suite.

`tests/oom` runs a set of programs once per allocation each makes, with
exactly that allocation failing, then once per allocation with it and every
later one failing, as SQLite's tests do. An allocation is a `malloc`, or a
value or block the context reuses. Every run must end in a result or an
exception, and free everything it allocated.

#### 2.4.2 Conformance

Conformance to PLS-315 rests on two kinds of evidence, and no other.

**Specification tests.** `make test-spec` runs the tests in `tests/spec`.

- Each is a small, self-checking script. It names the clauses of PLS-315
  (`docs/standards/3_15.md`) it exercises, imports only
  `tests/spec/harness.py`, and states its expectations directly. The suite
  needs neither a library nor another implementation.
- They run on `tests/run-spec`, a driver for the bare core with no library
  module. The host facilities a test reaches (Annex B) come through the
  harness's `host`: built on the engine primitives on spy, and on CPython's
  library facade on the oracle.
- `tests/spec_coverage.py` fails unless every clause of the normative
  chapters has a test.
- `make test-spec-oracle` also runs every test on the pinned CPython oracle,
  which must pass it.

Besides the tests written from the standard, three chapters come from
elsewhere:

| Chapter | Contents |
| --- | --- |
| `ports` | CPython's language test modules, each library import replaced by a core equivalent |
| `doctests` | CPython's doctest-based tests |
| `programs` | 1,356 programs (arithmetic, comparisons, argument binding, class creation, rounding, string search, template strings, asynchronous generator states, and more) with the output CPython 3.15 gives them |

**TLA+ models.** `make test-tla` model-checks the specifications in
`tests/tla`, then replays every transition of the bounded models on spy's
`tests/run-spec`, through the same harness `host`. `make test-tla-oracle`
replays them on the oracle too.

- The checker is TLC (fetched by `make tla-tools`; it needs a Java runtime),
  or `manyan` when it is installed. `MANYAN=` forces TLC.
- The models cover generator and coroutine methods, try/with control flow
  and exception context, name resolution, integer arithmetic, argument
  binding, unpacking, method resolution order, operator dispatch, attribute
  access, pattern matching, evaluation order, class creation, `yield from`,
  async generators, `except*`, the iteration protocol, `super()`, dict
  order, and object finalization and cycle collection.
- `SpyGC.tla` and `SpyGCGenerators.tla` also check spy's own
  memory-management algorithm against the language model, step for step.
- The [README](../tests/tla/README.md) states what these checks do and do
  not establish.

The pinned CPython 3.15.2 oracle (`make oracle`) validates tests and models.
No test needs it to run.

#### 2.4.3 Unicode

`make test-unicode` checks, for all 1,114,112 code points, representations,
printability, `chr`/`ord`, and identifier properties. It also checks 297,124
source/NFKC cases against the pinned oracle, and resolves all 160,282
character names and aliases through `\N{...}`. These checks pass. They do not
establish complete Unicode or unittest compatibility.

#### 2.4.4 Sanitizers

| Command | Runs `make test` under |
| --- | --- |
| `make sanitize` | AddressSanitizer (with its leak checker and its check for locals used after return) and UndefinedBehaviorSanitizer; also the Python package's tests |
| `make CC=clang SANITIZERS=memory sanitize` | MemorySanitizer: reads of uninitialized memory |
| `make CC=clang SANITIZERS=thread sanitize` | ThreadSanitizer: state that contexts on different threads share |

- Everything runs instrumented: the engine, `spy`, `spyc`, the programs
  `spyc` generates, and the packages' sandboxed worker.
- No report is recoverable. `tests/sanitize.c`, linked into every
  instrumented program, compiles in the options and appends every report to
  one file that must stay empty. A report therefore fails the run even from a
  process whose status or output a test ignores.
- Under AddressSanitizer, the context's allocation caches poison what they
  hold, so using a released value is reported even when its allocation is
  cached for reuse.
- The worker's own code is not leak-checked: leak checking needs `ptrace`,
  which the worker's sandbox refuses. The engine code the worker runs is
  leak-checked in every other program.
- Linux CI runs `make sanitize`. On the initial macOS host, AddressSanitizer
  hung during its own initialization; `make SANITIZERS=undefined sanitize`
  passed there.

#### 2.4.5 Fuzzing and coverage

`make fuzz` runs the libFuzzer targets ([fuzz/README](../fuzz/README)) for
`FUZZ_SECONDS` each, seeded from the examples and the specification tests:

- the engine through `exec`;
- the engine through `compile`;
- the engine with one allocation failing;
- `spyc`'s own bundling code.

`make fuzz-replay` then runs every input the fuzzers kept under
MemorySanitizer.

These tools report the memory errors that the tests and fuzzed inputs reach.
They cannot show that code nothing executes is free of them. `make coverage`
(clang) measures what `make test` and the package tests execute:

- It writes an annotated copy of every source under `.obj/coverage/html`.
- It fails unless every line of the engine sources runs, and lists by
  function the lines that do not (`tools/coverage.py`).
- CI runs it on macOS, so a change that leaves a line unexecuted fails there.

### 2.5 Upstream Cython tests

Download the pinned upstream sources, then run the adapter:

```sh
make upstream
make test-cython
```

`tests/upstream.json` pins Cython and CPython commits. Downloads remain in
ignored `tests/upstream` checkouts with their original licenses. The fetcher
does not overwrite tracked local modifications. The adapter verifies the
Cython commit and rejects modified tracked source.

The full adapter currently returns failure. To record the known failing
baseline without making the reporting command fail:

```sh
make cython-report
```

The report is `tests/results/cython.json`. It records file, docstring group,
example number, source location, upstream input, expected output, actual output
or error, and outcome. Skips, harness errors, and files needing another adapter
are separate from passes. The source module is evaluated unchanged for each
docstring group; examples then run in order in a persistent context. No imports,
decorators, assertions, or unsupported constructs are removed.

The pinned Cython checkout has 102 `.py` and 807 `.pyx` files directly in
`tests/run`, plus build fixtures and support files.

- The adapter covers static doctests from `.py` modules.
- `make cython-dynamic-report` also runs unchanged modules in isolated
  oracle processes, to discover runtime class docstrings and `__test__`
  groups. Its current result is 367 passing and 11,176 failing examples, with
  12 adapter-ineligible files and four discovery errors. The errors remain
  failures of the strict coverage gate.
- Cython's own runner also compiles extension modules, runs unittest cases,
  checks compiler diagnostics, and processes multi-file build tests. Those
  categories need separate support.

The current full adapter result is **343 passing and 11,107 failing examples**
from 89 attempted files; 13 other files were adapter-ineligible. Most failures
occurred while parsing their unchanged modules. This is a baseline, not a
near-complete language implementation. See the
[upstream test report](testing/cython.md) for the exact revision, inventory,
method, limitations, and reproduction commands.

### 2.6 Benchmarks

```sh
make clean
make bench
```

The lifecycle benchmark creates a context, parses and executes a hello-world
program with discarded output, and destroys the context. It reports average CPU
time across 20,000 iterations. It excludes process launch and terminal I/O.

On Apple M2, macOS arm64, Apple Clang 17, `-O2`, the recorded run at `af37fe2`
(the 0.6.0 release) measured 191 microseconds of CPU time per lifecycle
(three runs: 191.26, 193.55, 189.18 µs; 0.5.0 measured the same on that day). The Mach-O `__TEXT` segment was
1,392,640 bytes; the executable file was 1,509,472 bytes. These measurements
apply to this build. They do not establish x86 performance, a worst-case
latency bound, or the few-kilobyte size goal.

The [benchmark report](benchmark.md) compares whole-program wall time and
memory with CPython, PyPy, RustPython, PocketPy, Monty, and MicroPython on
core-language programs.

## 3 Specifications

### 3.1 Python language support

The target is [PLS-315:2026-draft2](standards/3_15.md). It has three
profiles:

- **Core**: the language.
- **Host services**: its Annex B host hooks.
- **CPython Extension compatibility**: the CPython C API and ABI.

The language edition, the engine release, and the upstream test revisions are
separate identifiers.

#### 3.1.1 Conformance

spy conforms to the Core profile of PLS-315. The evidence is
[Local tests](#24-local-tests), and nothing else. On the bare core:

- spy passes all 357 specification tests. `make test-spec-oracle` also runs
  them on the pinned CPython 3.15 build. Together they cover each of the 180
  clauses of chapters 6–29 and Annexes A–B.
- All 112 TLA+ models check. Of the 111 that replay on an engine, every
  transition passes on spy, as it does on the oracle.

Where PLS-315 leaves a choice to the host or the implementation, this
section states spy's choice.

Porting CPython's language test modules into `tests/spec/ports` continues.
A port that finds a difference is a defect in spy or in the standard, and is
fixed there.

spy has no CPython C API/ABI layer. That belongs to the Extension profile,
which spy does not claim.

#### 3.1.2 Overview

| Area | Support |
| --- | --- |
| Values | `None`, `NotImplemented`, `Ellipsis`, booleans, arbitrary-precision integers, doubles, complex numbers, bytes, UTF-8 strings, lists, tuples, dictionaries/frozendicts, sets/frozensets, bytearrays, memoryviews, ranges, functions, modules, basic classes/instances |
| Expressions | Arithmetic, bit operations, comparisons/chains, boolean operators, conditionals, calls, indexing/slicing, lambdas, assignment expressions |
| Template strings | `t`/`rt`/`tr` literals, native Template and Interpolation values, raw values and expression spelling, conversion metadata, evaluated format specifications, concatenation and iteration |
| Control flow | `if`/`elif`/`else`, `while`, `for`, loop `else`, `break`, `continue`, `return`, `assert`, `pass`, basic `with` |
| Assignment | Chained assignment, nested/starred unpacking, attribute/item targets, deletion, all augmented operators with in-place/reflected method dispatch |
| Functions | Positional-only and keyword-only parameters, writable `__defaults__`/`__kwdefaults__`, `*args`, `**kwargs`, call unpacking, recursion, lexical closures, `global`/`nonlocal`, decorators |
| Iteration | Builtin and user-defined iterators, list/dict/set comprehensions, generator functions, lazy generator expressions, `yield from`, `send`/`throw`/`close`, Python 3.15 starred comprehension elements |
| Async | Native coroutines, `async def`, `await`, `async for`, `async with`, async comprehensions/generator expressions, asynchronous generators, `asend`/`athrow`/`aclose`, `aiter` and `anext` |
| Objects | Metaclasses and namespace mappings, C3 and custom MROs, builtin value subclasses, `super`, class construction hooks, instance attribute interception, private-name mangling, instance/class attributes, bound/static/class methods, properties, descriptor access, `__new__`/`__init__` dispatch, calls, basic truth/string/iteration/indexing protocols |
| Comparisons | User-defined rich methods, reflected subclass priority, arbitrary comparison results, default `!=` delegation, identity shortcuts for container elements, `__contains__` |
| Exceptions | Basic exception classes/instances, `raise`, explicit causes and context suppression, bare re-raise, `try`/`except`/`else`/`finally`, exception groups and `except*`, subclass matching |
| Annotations and patterns | Lazy annotations, type parameters, type aliases, structural matching |
| Imports | Multiple/dotted imports, aliases, parenthesized import lists, package/relative imports, star imports, `__import__` hooks |
| Builtins | `print`, `len`, `range`, `str`, `repr`, `ascii`, `format`, `int`, `float`, `complex`, `bytes`, `bytearray`, `bool`, `list`, `tuple`, `dict`, `frozendict`, `set`, `frozenset`, `sorted`, `abs`, `pow`, `divmod`, `round`, `hash`, `bin`, `oct`, `hex`, `sum`, `min`, `max`, `all`, `any`, `iter`, `next`, `map`, `filter`, `zip`, `enumerate`, `reversed`, `ord`, `chr`, `type`, `super`, `isinstance`, `issubclass`, `getattr`, `setattr`, `delattr`, `hasattr`, `callable`, `id`, `slice`, `staticmethod`, `classmethod`, `property`, `dir`, `locals`, `globals` |
| Methods | List `append`, `extend`, `insert`, `pop`, `remove`, `clear`, `copy`, `reverse`, `sort`; list/tuple `count`/`index`; dictionary `get`, `keys`, `values`, `items`, `update`, `copy`, `clear`, `pop`, `popitem`, `setdefault`; str/bytes `startswith`, `endswith`, `find`, `rfind`, `index`, `rindex`, `count`; string `join`, `splitlines`, `isprintable`, `isidentifier`, and positional/named-field `format`; slice `indices`; numeric `conjugate`; integer `bit_length`/`bit_count` |
| Dynamic source | Code objects, three-argument `compile` in `exec`/`eval`/`single` modes, `eval`/`exec` with dictionary globals, mapping locals, and custom builtin dictionaries |

Fixed-width host conversions raise `OverflowError`. They never truncate
silently.

#### 3.1.3 Classes

Inheritance and construction:

- Classes use C3 multiple inheritance, explicit and zero-argument `super`,
  and lexical `__class__` cells.
- Construction calls `__set_name__` on a snapshot of the namespace, then the
  inherited `__init_subclass__`, and only then the class decorators.
- Plain `__init_subclass__` and `__class_getitem__` functions become class
  methods.
- Three-argument `type()` takes the same construction path.
- Metaclasses support `__prepare__`, `__new__`, `__init__`, custom `mro()`,
  and base resolution through `__mro_entries__`.
- Class namespace reads and writes honor mapping overrides. Native
  `type.__new__` accepts dictionaries, frozendicts, and their subclasses.
- Instantiating a class whose own `__abstractmethods__` is true raises
  CPython's `TypeError`, naming the methods in sorted order.

Calling a class:

- A class factory may return an unrelated object; `__init__` is then not
  called. A returned subclass instance uses its own initializer.
- `object.__new__`, `object.__init__`, and `BaseException.__new__` are
  available, with their allocation and type checks.
- Numeric, string, sequence, dictionary, and set subclasses keep an
  underlying builtin value.

Class metadata:

- Classes have `__firstlineno__` and `__static_attributes__`.
- `__name__` and `__qualname__` live outside the class `__dict__`.
- A class that introduces an instance dictionary or weak references gets the
  shared `<attribute '__dict__'>` and `<attribute '__weakref__'>`
  descriptors in its `__dict__`, following CPython's rules for builtin bases.
  `__weakref__` reads as `None`.
- Class `__dict__` is a live, read-only `mappingproxy`.

`__slots__`:

- A string, an iterable, or a mapping's keys.
- Slots become sorted, name-mangled `member_descriptor` attributes.
- Without a `__dict__` slot or a base with a dictionary, instances refuse new
  attributes, with CPython's messages.
- `__weakref__` and `__dict__` slots, conflicts with class variables, `int`
  and `bytes` bases, and conflicting slotted bases are all checked.

#### 3.1.4 Attributes and descriptors

- Descriptor lookup gives data descriptors precedence and supports
  `__get__`, `__set__`, and `__delete__`.
- Instance reads, writes, and deletions go through `__getattribute__`,
  `__setattr__`, and `__delattr__`. The explicit `object` methods give the
  default behavior. `__getattr__` follows a failed read.
- Implicit special-method lookup bypasses these interception hooks.
- Properties receive their class attribute name and have writable
  `__name__`.
- A custom `__class_getitem__` supports class subscription. Builtin generic
  aliases and unions use embedded intrinsic objects (see
  [3.1.12](#3112-not-yet-in-c)).
- Builtin types expose method descriptors and slot wrappers (`list.append`,
  `int.__add__`, `object.__repr__`) with CPython's reprs and names. They are
  created on first lookup and do not change implicit special-method dispatch.
- Builtin functions expose `__self__`. Functions, bound methods, and builtin
  method descriptors expose `__get__`.
- Builtin functions have `__doc__` text for slot wrappers and `None`
  otherwise, and a `__text_signature__` of `None`.
- A builtin base that comes before the defining class in the MRO supplies
  its own slot on attribute access, as CPython's type lookup does. Enum mixins
  such as `IntFlag` and `StrEnum` therefore resolve their methods correctly.
- Setting an attribute of a builtin object without `__dict__` raises
  CPython's three `AttributeError` forms. Unsupported orderings name the
  operator and the types.
- `isinstance` and `issubclass` follow `Objects/abstract.c`: exact types
  check the MRO, tuples are searched, other targets use `__instancecheck__`
  or `__subclasscheck__`, and objects with a tuple `__bases__` act as
  classes, with recursion limits on cyclic bases.
- Object reduction (`object.__reduce__`, `__reduce_ex__`, `__getstate__`)
  follows `typeobject.c`: `__getnewargs_ex__`/`__getnewargs__`, `__dict__` and
  slot state, list and dict items, and `copyreg` (imported from the host when
  needed) for protocols below 2. The `pickle` module is a library facility
  outside the core; the spec tests check the reduction protocol through a
  core stand-in.

#### 3.1.5 Builtins

The builtins module provides every CPython 3.15 builtin except:

- `input`, which needs a host stream;
- `help`, `copyright`, `credits`, and `license`, which come from the `site`
  module.

Builtin argument counts and keywords are checked with CPython's messages.
Particular builtins:

- **`open`** reaches only host directories mounted with `spy_mount` (see
  [Host services and limits](#346-host-services-and-limits)). Without a
  mount, every path raises `PermissionError`.
  - It returns `_io`-named `FileIO`, `BufferedReader`, `BufferedWriter`,
    `BufferedRandom`, and `TextIOWrapper` objects.
  - They have CPython's modes, argument validation, reprs, `with` and
    iteration, `readline`/`readlines`, `seek`/`tell`/`truncate`, universal
    and explicit newline handling, and `UnsupportedOperation` (an `OSError`
    and a `ValueError`).
  - Buffered objects pass straight through to the descriptor.
  - Text files decode `utf-8` (the 3.15 default), `latin-1`, or `ascii`: the
    codecs `str.encode` supports.
  - Integer descriptors and `opener` are refused.
- **`exit` and `quit`** raise `SystemExit` with their code.
  `SystemExit.code` follows CPython.
- **`__build_class__`** creates a class as a class statement does, calling an
  ordinary function for the body.
- **`__lazy_import__`** returns a lazy import object, as the `lazy import`
  statement does.
- **`breakpoint`** calls the `breakpointhook` of a loaded `sys` module. It
  raises "lost sys.breakpointhook" when that hook is absent, and returns
  `None` when no `sys` is loaded.
- **`sentinel`** (new in 3.15, PEP 661) creates unique named objects. They
  record their creating module, copy as themselves, reduce to their name, and
  form unions with `|`.
- **`compile`** accepts `flags`, `dont_inherit`, `optimize`, `module`, and
  `_feature_version`, with CPython's validation. The flags do not change the
  resulting code. `PyCF_ONLY_AST` raises `NotImplementedError`.
- **`types.FunctionType`** creates a function from a code object.
- **`sorted` and `list.sort`** sort stably by key, in either direction,
  evaluating each key once. In-place sorting detects mutation by callbacks
  and restores the list.

#### 3.1.6 Exceptions

- **Fields.** `args`, the chaining attributes, and each class's members
  (such as `errno`, `msg`, `value`, or `name`) are kept outside the instance
  `__dict__`, as CPython's C members are. Deleting one follows CPython. The
  class attributes are `member_descriptor` and `getset_descriptor` objects
  with `__get__`, `__set__`, and `__delete__`.
- **`OSError(errno, strerror, filename, winerror, filename2)`** follows
  CPython: the errno selects the subclass, the attributes are set, a filename
  shortens `args`, and `str` gives `[Errno N] message: 'name'`.
- **`ImportError`** accepts `name`, `path`, and `name_from` keywords, and
  keeps a lone argument as `msg`. **`AttributeError`** accepts `name` and
  `obj`; **`NameError`** accepts `name`. Failed attribute and name lookups
  fill these attributes, as CPython does.
- **Unicode errors** take and expose `encoding`, `object`, `start`, `end`,
  and `reason`. Codec failures raise them with those fields, covering a run
  of unencodable characters.
- **Groups.** `BaseExceptionGroup`'s `message` and `exceptions` are
  read-only. A group accepts any sequence and keeps the repr of a custom one.
- **Reduction.** `__reduce__` and `__setstate__` follow `BaseException`,
  `OSError`, `ImportError`, and `AttributeError`.
- **Notes.** `add_note` and exception notes are supported. A failed
  `__set_name__` callback keeps its exception and receives a note naming the
  descriptor and the class.
- **Syntax errors** expose the message, filename, source line, and position.
  Their string form includes the basename and line when available.

Tracebacks are built as CPython builds them:

- An error adds an entry for each frame it passes through.
- `raise exc` continues `exc`'s traceback; a bare `raise` adds none.
- Entries have `tb_next` (assignable, with loop detection), `tb_frame`,
  `tb_lineno` (the statement's line), and `tb_lasti` (always 0: there is no
  bytecode).
- `__exit__`, `generator.throw`, `with_traceback`, and
  `types.TracebackType(...)` accept and pass them on.

#### 3.1.7 Bytes, buffers, and sequences

Bytes and bytearrays:

- Bytes support literals, sequence operations, construction from an integer
  or an iterable, and the string/bytes method families.
- Bytearray methods include `resize` and Python 3.15's `take_bytes`. Bounds
  and storage are rechecked after conversion callbacks.
- A bytearray with live exports refuses to resize, raising CPython's
  `BufferError`.
- `bytes` and `bytearray` expose `__buffer__`, and bytes consumers accept
  views.

`memoryview`:

- Wraps bytes, bytearrays, other views, and objects with `__buffer__`.
- Supports native struct formats (including `e`, `?`, and `P`), and `cast`
  between 1-D and N-D shapes.
- Provides indexing, slicing, item assignment, comparison, hashing,
  `tolist`, `tobytes`, `hex`, `toreadonly`, `release`, and the
  context-manager protocol.
- Not supported: struct-module formats beyond native single items,
  multi-dimensional sub-views, and CPython's allocation introspection.

Codecs: encoding and decoding provide the core codecs of PLS-315 Table 23-1.
spy's host supplies no others.

Iterators:

- Every intrinsic iterator has its own type, with `__reduce__` and
  `__setstate__` as 27.1.1 gives.
- The sequence, dict, set, range, and reversed iterators provide CPython's
  `__length_hint__`.
- `list()`, `list.extend`, and `bytearray.extend` pass on errors from a user
  iterable's `__len__` or `__length_hint__`, as `PyObject_LengthHint` does.

Slicing and ranges:

- Lists, tuples, strings, bytes, and ranges support slicing.
- Range bounds, indices, steps, and `slice.indices()` lengths are
  arbitrary-precision integers.
- Ranges support iteration, reverse iteration, integer membership, equality,
  `count`, and `index`. `len` rejects lengths larger than the host's size
  type.
- Slices compare their three components lexicographically, keeping identity
  shortcuts and user-defined comparison results.

#### 3.1.8 Hashing, dictionaries, and mappings

Hashing:

- A class that defines `__eq__` without `__hash__` becomes unhashable.
- `hash()` calls user-defined hash methods, validates their results, and
  normalizes oversized integers.
- Numeric hashes keep equality across integers, floats, and complex numbers.
- Tuples cache successful hashes. Slices and ranges are hashable when their
  components are.
- String and bytes hashes use unsalted FNV-1a with its high half folded into
  the low. PLS-315 leaves this to the implementation. There is no
  per-process randomization.
- The numeric and compound hash algorithms adapt CPython's implementation
  under its [license](licenses/python.txt).

Dictionaries and sets:

- Entries store their hashes. Maps with more than eight entries also keep an
  open-addressed index by hash; smaller ones scan the entries.
- A dict counts the keys it removes, and its iterators compare that count.
  Once keys were removed and as many added, the next `__next__` raises
  "dictionary keys changed during iteration" instead of ending (PLS-315
  26.1.4).
- `keys`, `values`, and `items` return live views. Keys and items views are
  set-like, and their `mapping` is a read-only native `mappingproxy`.

Mapping proxies forward mapping methods and support generic aliases. Before a
comparison with an arbitrary reflected-equality callback, they copy an exact
dictionary, following Python 3.15. They are implemented in C.

Frozen dictionaries:

- `frozendict` shares dictionary lookup, views, unpacking, and pattern
  matching.
- Its hash combines the stored key hashes with the value hashes, and caches
  the completed result.
- An exact frozen copy may reuse the original value; a subclass copy produces
  a plain frozen mapping.
- `eval` and `exec` accept frozen globals that already have a
  `__builtins__` entry, and reject writes and deletions.

#### 3.1.9 Strings, formatting, and Unicode

- **F-strings** support expressions, debug fields, conversions, nested format
  specifications, raw literals, and generator suspension inside fields.
- **`format` and `format_map`** follow CPython's parser: automatic and manual
  numbering, attribute and index field paths, conversions, nested
  replacement fields in specifications (two levels), and CPython's
  diagnostics.
- **The format-spec mini-language** for `str`, `int`, `bool`, `float`, and
  `complex` is ported from CPython: fill code points, alignment, sign, `z`,
  `#`, zero padding, Unicode digit widths, `,`/`_` integer and fractional
  grouping, every presentation type, the short float repr, and CPython's
  diagnostics. `n` uses the C locale.
- **Percent formatting** for `str`, `bytes`, and `bytearray` follows
  CPython's conversions, flags, `*` widths and precisions, mapping keys, and
  diagnostics.
- **Unicode data.** Escaping, printability, identifier properties, and
  `\N{...}` escapes use checked-in Unicode 17.0.0 data. `\N{...}` takes names
  and aliases, case-insensitively; Hangul and derived ideograph names are
  computed. Normalization functions (`unicodedata`) are a library facility
  outside the core.
- **Template strings** are C objects with read-only `strings`,
  `interpolations`, and `values` attributes.
  - Interpolations keep `value`, `expression`, `conversion`, and
    `format_spec`. Constructing a template does not call the value's
    conversion or formatting methods.
  - Iteration omits empty literal strings.
  - The Template and Interpolation types are final. They can be obtained
    without a library import, as `type(t'')` and
    `type(t'{0}'.interpolations[0])`. The standard-library
    `string.templatelib` package is not part of the core.

#### 3.1.10 Source text

- Byte sources, CLI files, and imports honor encoding comments on the first
  or second line, and UTF-8 BOMs. Unicode string sources ignore encoding
  comments.
- UTF-8, ASCII, Latin-1, ISO-8859-15, and unicode_escape decoding is
  native. Other source encodings are left to the host.
- The lexer rejects invalid UTF-8.
- CR and CRLF become LF before parsing, including inside string literals.
- Indentation uses eight-column tab stops and rejects inconsistent mixing of
  tabs and spaces.
- Source identifiers are NFKC-normalized before scope analysis and
  private-name mangling. Dynamic string attribute and keyword names keep
  their original spelling.

Future statements are checked as CPython's compiler checks them:

- They must come first, after at most a docstring, and name a known feature.
  `braces` is "not a chance".
- `barry_as_FLUFL`, or `compile()`'s `CO_FUTURE_BARRY_AS_BDFL` flag, makes
  `<>` the inequality operator.
- The statement still imports `__future__` when a host provides it, and
  binds nothing otherwise.
- Under `from __future__ import annotations` (PEP 563), annotations become
  strings, written as CPython's AST unparser writes them. Functions return
  them from `__annotate__`; module and class bodies store them in an eager
  `__annotations__` dict.
- `compile()`, `exec()`, and `eval()` inherit the running code's future
  statements unless `dont_inherit` is true.

Syntax errors:

- These follow CPython's lexer and `invalid_*` grammar rules: parameter
  lists; assignment, deletion, loop, `with`, and keyword-argument targets;
  `assert` and condition `=` typos; starred arguments; string prefixes;
  unbalanced brackets; missing indented blocks; and conditional expressions.
- Errors that CPython raises from its compiler (`'break' outside loop`,
  `'return' outside function`, misplaced `async for`, `async with`, and
  `await`) are raised only after the whole source parses.
- Compiler-phase `SyntaxError`s from `compile()`, `exec()`, and `eval()`
  strings have no `text`, as in CPython.
- Some diagnostics still differ from CPython. These are open compatibility
  issues, not changes to the standard.

Nesting limits follow CPython:

- 200 levels of brackets ("too many nested parentheses").
- An expression too deep for the parser raises `MemoryError` ("Parser stack
  overflowed").
- Runs of prefix operators and long operator chains do not use C stack per
  operator, and the compiler's checks are bounded by stack use.

#### 3.1.11 Code, scopes, and suspension

Namespaces:

- Module and class namespaces and explicit execution mappings are live.
  Optimized function locals are snapshots.
- Class and execution locals may be arbitrary mappings. Globals must be
  dictionaries, subclasses included.

Code objects:

- They expose argument counts, names, filenames, first-line metadata, and
  CPython's sorted `co_freevars` and `co_cellvars`, including names passed
  through to nested scopes and the implicit `__class__`.
- They are cached per parsed definition, so functions made from the same
  definition share one code object. `gi_code`, `cr_code`, and `ag_code` keep
  that identity after the suspended instance closes.
- They hold parsed syntax and internal generator instructions. There is no
  public bytecode format.
- A function's `__code__` may be replaced.

Closures and dynamic execution:

- A function's `__closure__` holds cells that read and write the defining
  scope's variable. `types.CellType` cells compare by contents.
- `exec` and `eval` run a code object, a function's included, as a call with
  no arguments. Code with free variables is rejected there, as in CPython.
- A closure given to `exec`, `eval`, or `types.FunctionType` must consist of
  cells bound in the function's defining scopes, with the same globals,
  because spy functions share their defining environment rather than holding
  cells.

Generators:

- They keep operands, loop state, active exceptions, and pending cleanup
  across suspension.
- An explicit `close()` runs cleanup and returns the generator's return
  value.
- A suspended generator that becomes unreachable, by reference release or
  cycle collection, is closed first (27.2.4).
- Frames are live objects.
- `yield` may appear in any expression position, class bases included.
  Raise expressions and explicit causes may yield or await.
- Assertions keep their original message objects.

Coroutines and asynchronous generators:

- They share the generators' owned suspension stacks.
- Async context-manager exits may suspend during a return, a loop exit, and
  exception handling.
- Asynchronous-generator operation objects reject concurrent operations and
  reuse.
- Comprehensions run on the same machinery, nested async clauses and awaited
  elements and filters included.
- spy's host provides no HostWarn, so warnings such as an unawaited
  coroutine's are ignored (PLS-315 B.4.1).
- The core provides no event loop.

Parenthesized context-manager lists work for synchronous and asynchronous
managers.

#### 3.1.12 Not yet in C

The parser, evaluator, value storage, and collector are C11. Generic and
related intrinsic objects still use Python source embedded in
`spy-intrinsics.h`, generated from `intrinsics.py` and interpreted by `spy`
on first use. This adds no external dependency and needs no Python to build.
It is a remaining gap against the requested C11-only implementation of
language semantics.

### 3.2 Modules

The host supplies modules through a module-loader callback. The callback
receives the context and returns the source as an owned bytes value. The
engine decodes and parses it like a file (PEP 263, BOM, null-byte check).

Loading:

- For `pkg.mod`, the core first asks the callback for `pkg.mod.__init__`,
  then for `pkg.mod` if there is no package source.
- Asked for `pkg.mod`, the callback may register it with `spy_new_module`
  instead of returning source. The import then runs that init, as it does for
  a native module ([3.4.9](#349-native-modules)).
- An embedded context has no default filesystem loader.

The `spy` command's loader:

- Maps dots to directory separators and reads the `.py` file under the
  original script's directory, or under the current directory for stdin and
  `-c`.
- A regular file with `.so` in place of `.py` (`.dll` on Windows) is a
  native module and comes first, as CPython's extension modules do. A
  package's `__init__` is always source.
- Does not provide module specs, package search paths, meta-path finders, or
  CPython extension modules. These are host services (PLS-315 Annex B).

The module cache:

- Each context caches modules by name.
- A module is cached before it runs, so simple circular imports work. A
  failed initialization removes its entry.
- As in importlib, an import returns the module that `sys.modules` holds once
  the source has run. A submodule that importing its parent placed in
  `sys.modules` needs no loading.

Modules:

- Each source module has a namespace, `__name__`, and `__package__`.
  Packages have `__path__`, but the current loader does not search it.
- Relative imports use `__package__`.
- A module-level `__getattr__` supplies missing attributes (PEP 562).
- Import statements call the frame's builtin `__import__`. The default one
  loads sources through the callback.
- The `builtins` module is the context's builtin namespace itself, and needs
  no loader.
- A failed import sets `ImportError.name`. A missing `from` name reports the
  module, its file, and `name_from`, as CPython does.

Lazy imports (Python 3.15 `lazy import` and `lazy from ... import`):

- At module level, outside `try` blocks, they bind `lazy_import`
  placeholders.
- Reading a placeholder through a module global, a class namespace, or a
  module attribute calls `__import__` and replaces the binding. A failure is
  chained to an `ImportError` cause naming the lazy import.
- A `from` import of an already-loaded module binds the attribute directly.
- `sys.set_lazy_imports('all')` makes every eligible module-level import
  lazy, and `sys.set_lazy_imports_filter` may keep any of them eager (PLS-315
  B.1.4).

### 3.3 Standard library and host services

The core engine (`spy.c`, `libspy.a`) provides the language and its builtins,
and no module but `builtins`. A program reaches every intrinsic through the
language; PLS-315 Annex C lists the Core expressions. Every other module is
the host's choice.

#### 3.3.1 Modules a host registers

A host registers modules with `spy_new_module`. Three kinds are shipped:

| Module | Registered by | Contents |
| --- | --- | --- |
| `_spy` | Any host, with `spy_init_primitives` | The engine primitives for modules written in Python: the module cache, frames, the recursion and integer-string limits, the handled exception, collection, the weak table, host output, the command line, and the tokenizer |
| `sys` | `spy_std_init_module` or `spy_std_init` (`spy-std.c`, `libspy-std.a`, `spy-std.h`) | The standard layer, written on those primitives and specified after CPython 3.15 by [PLS-STD-315](standards/std.md) |
| Native modules | `spy_std_init`, which loads them with `spy_std_load_native` | One module in a shared library ([3.4.9](#349-native-modules)) |

A context where no host registered `_spy` has no such module. The standard
layer's Python sources live in `modules/` and are embedded into
`spy-std-modules.h`. An import finds them before the host loader, needs no
loader, and parses each only on first use.

Who registers what:

- The `spy` command calls `spy_std_init`.
- A program `spyc` builds registers the standard modules it imports.
- The conformance driver `tests/run-spec` registers only `_spy`.

#### 3.3.2 `sys`

Before and after a `sys` module is loaded:

| | Without `sys` | With `sys` |
| --- | --- | --- |
| `print`, interactive display | The host output callback; display uses its default | `sys.stdout` |
| `breakpoint` | Returns `None` | Calls `sys.breakpointhook` |

(PLS-315 Annex B.) When a host registered `sys` but no program imported it,
the first unraisable exception imports it, so the report appears as under
CPython, whose `sys` is always loaded.

`sys` keeps the runtime state natively:

- `modules`, `exception()`, the recursion and integer string-conversion
  limits, and reference counts.
- `stdout` and `stderr` streams that write to the host's output and error
  callbacks.
- `implementation.name` is `smallpython`.
- `_getframe()` returns frame objects for running calls: functions,
  generators, class bodies, and modules. A function frame's `f_locals` is a
  write-through `FrameLocalsProxy`, as in PEP 667. Line numbers are those of
  the executing statement.

The engine keeps these settings, and `sys` changes them through the
`_spy._setting` primitive:

- the lazy-import mode and filter;
- the asynchronous-generator hooks;
- coroutine origin tracking;
- the hook that receives unraisable exceptions;
- the trace and profile functions. Trace functions see the `'call'`,
  `'line'`, `'return'`, and `'exception'` events of Python frames.

`sys.excepthook` and `sys.unraisablehook` write CPython's traceback display,
without source lines.

[PLS-STD-315](standards/std.md) specifies every name of `sys` after CPython
3.15, and lists those not provided: `sys.monitoring`, audit hooks, and the
thread and extension-module interfaces, among others. `tests/std.py` checks
the rest against CPython.

There is no `gc` module. The engine collects cycles by itself
([4.4](#44-garbage-collection)), and a host controls collection through the
C API ([3.4.7](#347-collection)).

#### 3.3.3 Weak references

No `weakref` module is built in. The engine keeps weak references for its
hosts:

- `_weak_bind(target, reference, callback)` registers a reference object in a
  per-context table of borrowed (referent, reference) pairs.
  `_weak_get(reference)` reads its referent back.
- Weakly referenceable, as in CPython: instances of classes without
  `__slots__` (or with `__weakref__` in them), classes, functions, bound
  methods, builtin functions, sets, frozensets, generators, coroutines, code
  objects, memoryviews, and modules.
- Releasing a referent, or collecting it in a cycle, clears its references
  and queues their callbacks. They run at the next statement boundary. A
  collection clears the references with a callback before it runs the
  finalizers of the garbage it found, so no callback sees a resurrected
  object; the others answer until the object is freed.
  Callback exceptions are discarded, because there is no error stream.
- Closures keep their whole defining environment alive, so a closure can
  keep a local that CPython would have released.

#### 3.3.4 Everything else

Other standard-library modules are not built in. Core `print` needs an output
callback, and other source imports need a loader; an embedding application
opts into those. Optional Python-level wrappers of C libraries are future
work.

Leaving out the standard library does not remove the requirements for
classes, exceptions, Unicode, imports, or async syntax. The specification
keeps those in the Core profile, and treats unavailable host services
separately.

### 3.4 C API

This section explains how the API fits together. [api.md](api.md), generated
from `spy.h`, states each declaration's contract.

#### 3.4.1 Contexts

`spy_context_new()` returns an independent context or `NULL` on allocation
failure. `spy_context_free()` destroys it and all remaining values. Contexts
have no process-global mutable runtime state. Use independent contexts on
different threads; do not concurrently enter one context. `spy_set_opaque` and
`spy_get_opaque` attach one host pointer to a context, so callbacks such as a
module init can find the host object that owns the context.

The API has no runtime shared between contexts. One `SPYContext` owns its heap,
globals, module cache, errors, callbacks, and execution budget.

#### 3.4.2 Values and ownership

`SPYValue *` is opaque. Returned values are owned unless explicitly documented
otherwise. `spy_retain` adds a reference and `spy_release` removes one. Lists and
globals retain values assigned to them. Native arguments are borrowed. Values
cannot cross contexts. Release externally held values before context teardown;
using one afterward is invalid.

Constructors include `spy_none`, `spy_bool`, `spy_int`, `spy_float`,
`spy_string`, `spy_bytes`, and `spy_list`. Accessors include `spy_type`, `spy_as_int`,
`spy_as_float`, `spy_as_string`, `spy_as_bytes`, and `spy_truth`.
The fixed-width `spy_as_int` accessor raises `OverflowError` for larger integers. `spy_repr` returns an owned
string. `spy_list_append` mutates lists and rejects tuples.

#### 3.4.3 Native functions

Register a callback with `spy_define`. Its signature is:

```c
SPYValue *callback(SPYContext *ctx, size_t argc,
                   SPYValue *const *argv, void *data);
```

Return an owned value on success. On failure, set an error with `spy_error` and
return `NULL`. Callback user data belongs to the host. `spy_call` invokes a
language or native callable. The example in `examples/embed.c` shows argument
validation, checked arithmetic, registration, evaluation, and cleanup.

#### 3.4.4 Errors

API failures use `NULL` or `-1`, with details available through
`spy_error_type`, `spy_error_message`, `spy_error_filename`, and
`spy_error_line`. These strings belong to the context. `spy_clear_error` resets
them. `spy_error_value` returns the pending exception object, creating it from
the record if needed, and leaves the error set. `spy_raise` raises an exception
instance or class, so a native callback can fail with any exception.

#### 3.4.5 Evaluation

| Function | Returns |
| --- | --- |
| `spy_eval(ctx, source, filename)` | The final expression's value, or `None` |
| `spy_exec` | A status; the value is discarded |
| `spy_eval_interactive` | As `spy_eval`, and displays each non-`None` expression through the output callback |

- Interactive display covers expressions inside interactive loops and
  conditionals. Function and class bodies execute as usual. A successful
  display updates the builtin `_`.
- All three keep globals between calls.
- A new top-level evaluation clears the previous error and resets the step
  counter.
- Parsing precedes all execution. A runtime error does not roll back the
  assignments before it.

Use `spy_get_global` and `spy_set_global` for host access to global bindings.
Do not recursively call `spy_eval` from a callback on the same context.

#### 3.4.6 Host services and limits

The core installs no host service by itself. Every host callback receives
the context first, except the interrupt and a native's release callback,
which must not call into the engine. A callback that fails may set its own
error, which takes the place of the engine's generic one.

**Streams.**

| Function | Installs |
| --- | --- |
| `spy_set_output` | Text output, and a flush callback sharing its data pointer; without one, output is unbuffered |
| `spy_set_error_output` | Error text (the standard layer's `sys.stderr`), with its own write and flush callbacks; without them, error text shares the output callbacks |
| `spy_set_input` | The line reader behind `input()`. It returns an owned str, with or without its line ending, or `NULL` at the end of input. Without a reader, `input()` raises `EOFError` |
| `spy_set_module_loader` | Module source loading ([3.2](#32-modules)) |

- `print(file=...)` uses the Python object's `write` and `flush` methods.
- `spy_std_report` reports the pending exception through `sys.excepthook`,
  which writes CPython's traceback display to `sys.stderr`.
- The `spy` command reads standard input for `input()`, and reports uncaught
  exceptions with `spy_std_report` on standard error.

**Modules.** `spy_new_module(ctx, name, init)` registers a module. An import
finds it before the loader.

- The first import creates the module object, with `__name__`,
  `__package__`, and `__builtins__` set, and calls `init(ctx, module)`.
- `init` fills it, with `spy_set_attr`, `spy_native` values, or Python source
  through `spy_exec_module`, and returns 0, or -1 with an error set to fail
  the import.
- An init that sets `__path__` makes a package, whose submodules register
  under dotted names.

**Files.** `spy_mount(ctx, directory, path, flags)` lets `open` reach a host
directory at an absolute guest path, or at the directory's own resolved path
when `path` is `NULL`. Nothing else is reachable:

- A guest path is normalized lexically and must fall inside a mount, the
  longest matching one. It is then resolved on the host with `realpath`, so
  `..` and symbolic links cannot leave the mount. Files are opened with
  `O_NOFOLLOW`.
- Relative paths start at the first mount.
- `SPY_MOUNT_READ_ONLY` refuses writes with `EROFS`.
- The context owns every descriptor `open` creates, and closes those left
  open when it is freed. Other descriptors, such as the process's standard
  streams, are unreachable.
- File access needs a POSIX host. Elsewhere, `spy_mount` and `open` raise
  `OSError`.

The `spy` command mounts its working directory at its own path.

**Command line.** `spy_set_argv(ctx, argc, argv, orig_argc, orig_argv)`
gives the context the program's command lines.

- When the standard layer's `sys` is first imported, it copies them into
  `sys.argv` (the script's) and `sys.orig_argv` (the whole command line the
  process was started with).
- The strings are copied and decoded as UTF-8 with `surrogateescape`, so any
  bytes are kept. It returns 0, or -1 with `MemoryError`.
- Until a host sets them, both lists are empty.
- Programs that `spyc` builds set them from `main`, and the `spy` command
  from its arguments ([2.3.1](#231-spy-interpreter)).

**Optimization.** `spy_set_optimize` sets the optimization level (PLS-315
B.6), as `python -O` and `-OO` do. At 1, `assert` statements are not
evaluated and `__debug__` is `False`. At 2, docstrings are not kept either.
`compile(optimize=-1)` uses it.

**Limits.** `spy_set_limit(ctx, limit, value)` sets each limit, and
`spy_get_limit` reads it back. A value out of range, or an unknown limit,
fails with `ValueError`.

| Limit | Bounds |
| --- | --- |
| `SPY_LIMIT_STEPS` | The steps of each outermost `spy_eval`, `spy_eval_interactive`, `spy_exec`, `spy_exec_module`, `spy_call` or `spy_call_keywords`; zero means unlimited |
| `SPY_LIMIT_MEMORY` | The bytes the engine holds, values and their storage. A level, not a budget: it is not refilled per call. Zero means unlimited; `spy_memory_used` returns the count |
| `SPY_LIMIT_OUTPUT` | The bytes each outermost call writes to the output and error streams; zero means unlimited |
| `SPY_LIMIT_RECURSION` | The recursion limit (PLS-315 B.6); a program with `sys` can change it too |
| `SPY_LIMIT_INT_DIGITS` | The int-string conversion limit (PLS-315 B.6); likewise |
| `SPY_LIMIT_STACK` | The bytes of C stack the engine may use before `RecursionError`: 4 MiB by default, for a host that runs it on a smaller stack, such as a thread or WebAssembly |
| `SPY_LIMIT_PAUSE` | With 1, a spent step budget or an interrupt pauses instead of stopping (below) |
| `SPY_LIMIT_COLLECTION` | When automatic collection becomes due ([3.4.7](#347-collection)) |

A step is a unit of bounded work ([metering.md](metering.md)):

- one per Python call, and per 8 nodes of the body it runs;
- one per loop pass, and per item a native loop takes;
- one per 64 bytes of source parsed, or of a large block allocated (per 8
  elements of an array, so every target spends the same);
- for native work that only reads, such as comparing, searching or hashing,
  in proportion to its operands.

A host function calling back shares its caller's budget. `spy_steps_used`
returns the steps the running or last outermost call spent. Calls and native
iteration spend only while a limit, an interrupt or a trace function is set.

**Interrupts.** `spy_set_interrupt` installs a callback that the engine polls
at the first call, statement or native iteration after every 4096 steps, and
inside long multiplication, division, integer formatting and sorting. A
nonzero return stops the call. The engine reads no clock: a host bounds wall
or CPU time, or offers a cancel button, by reading its own in the callback,
which must not call into the engine.

**Stopping.** A spent budget, a refused allocation, output past its limit, or
an interrupt stops the call:

- Every further step fails, with `RuntimeError` (steps, output, interrupt)
  or `MemoryError` (memory). No handler or `finally` body runs.
- Finalizers that become due wait for the next outermost call, which runs
  normally.
- `spy_stopped` then returns `SPY_STOP_STEPS`, `SPY_STOP_MEMORY`,
  `SPY_STOP_OUTPUT` or `SPY_STOP_INTERRUPT`, and zero after any other call.
  This tells a stop from the same error raised by the program.

**Pausing.** With `SPY_LIMIT_PAUSE` set to 1, a spent step budget or an
interrupt pauses an outermost `spy_eval` or `spy_exec` instead of stopping it
([metering.md](metering.md) 3.8).

- The call returns `NULL` (`spy_exec` -1) with no error set, and `spy_paused`
  returns `SPY_STOP_STEPS` or `SPY_STOP_INTERRUPT`.
- `spy_resume(ctx)` runs it on from the step where it paused, with fresh
  budgets. It returns the call's value, or `NULL` with an error, or `NULL`
  paused again.
- A call pauses only at a step where its frames are all on the engine's
  machine. A pause that becomes due inside native code, such as an import,
  `exec` or a host function, waits until that code returns. A further budget
  spent before then stops the call, except one spent parsing or compiling
  source or charging a body's length as it is entered.
- Code compiled while the limit is set gives every operator, subscript and
  f-string field a step of its own, so their special methods pause too. Set
  the limit before running the code.
- Other calls may run while one is paused. Freeing the context stops a
  paused call.

**Policy.** `spy_set_policy` installs a callback asked before each sensitive
action, as CPython's audit hooks (PEP 578) are. It receives an event name and
a tuple of the event's arguments:

| Event | Arguments | Asked |
| --- | --- | --- |
| `open` | file, mode | Before a file is opened |
| `import` | name | Before a module first loads; not when the module cache serves it |
| `exec` | the source | Before `exec`, `eval` or `compile` parses a string |
| `input` | the prompt, if given | Before `input` writes it |

- Imports that the standard layer makes are events too: `sys` imports
  `_spy`.
- A zero return allows the action. Any other refuses it with
  `PermissionError`, unless the callback set an error of its own.
- Hosts ask the same callback about their own actions, such as a network
  request from a host function, with `spy_policy_check(ctx, event, args)`.
  It returns 0 when no policy is set.
- The core itself has no network access.

**What limits do not do.** Budgets bound what a program can spend: steps,
the bytes the engine holds and, through the interrupt, time. The policy
bounds what it may reach. Neither makes a context an isolation boundary: the
program runs in the host's process, so a defect in the engine can reach the
host. For untrusted programs, the packages' worker
([packaging/protocol.md](packaging/protocol.md)) adds a process and the
operating system's sandbox around the context.

#### 3.4.7 Collection

The engine collects cycles by itself. A collection becomes due when the
engine takes memory for new values while two things hold since the last
collection:

- the values that can form cycles (everything but small integers and
  floats) have grown by `SPY_LIMIT_COLLECTION` (2,000 by default), and
- the memory the engine holds has doubled.

The next statement boundary then runs the cycle collector
([4.4](#44-garbage-collection)). A heap that grows only in numbers is never
scanned, and the doubling keeps the total cost of collecting linear in what a
program makes. `spy_set_limit(c, SPY_LIMIT_COLLECTION, 0)` turns automatic
collection off, for a host that wants finalizers to run only when it asks.

`spy_collect` runs the collector now and returns the number of values
collected; values the host retains are roots. `spy_live_values` reports the
current value count. Context teardown frees the remaining cycles, whether or
not any collection ran.

#### 3.4.8 Stability

`SPY_VERSION` is the header's version, and `spy_version()` the library's.

- From 0.8.0 on, releases with the same major version are compatible, 0.8
  and later 0.x releases counting with 1.x. Before 0.8, only releases with
  the same minor version were.
- A later compatible release only adds functions, callback types, and
  enumeration constants (appended, so existing values keep their numbers).
  It never changes or removes a declaration.
- A declaration is removed only in an incompatible release, after one
  release that marks it deprecated in `spy.h`. The Changelog lists every
  incompatible change.
- `make check-api` enforces this against the last release tag, by compiling
  that release's declarations against the current header. It also requires
  every declaration to be documented, and `libspy.a` to export exactly the
  functions `spy.h` declares.
- 0.8.0 made the last incompatible changes planned. From it to 1.0.0 the API
  and ABI stay compatible under these rules, and 1.0.0 declares them stable.

The promise covers `spy.h` only. `spy_init_primitives` is part of it, but the
names it puts in `_spy` serve the standard layer and may change in any
release. Hosts and their Python code should reach those facilities through
the standard layer's `sys` and the C API, not `_spy`. spyc, which ships with
the engine and is built against it, is the one program outside the standard
layer that uses them.

#### 3.4.9 Native modules

A native module is a shared library that defines one module: a program
imports it without rebuilding its host. Its
source includes `spy-module.h` and marks the module's init, a
`SPYModuleInit` named `spy_init_` and the module's last name, with
`SPY_MODULE` ([examples/fib.c](../examples/fib.c)):

```c
#include "spy-module.h"

SPY_MODULE int spy_init_fib(SPYContext *c, SPYValue *module) {
    SPYValue *function = spy_native(c, "fib", fib, NULL, NULL);
    int status = function ? spy_set_attr(c, module, "fib", function) : -1;
    spy_release(function);
    return status;
}
```

```sh
cc -shared -fPIC -DSPY_SHARED_MODULE -I. examples/fib.c -o examples/fib.so
bin/spy examples/test_fib.py
```

The same source builds two ways:

- **With `SPY_SHARED_MODULE` defined**, every `spy.h` call goes through a
  table of function pointers that the host hands the library as it loads it.
  The library needs no symbol from the engine and exports only `spy_module`
  and its init. It therefore loads into the statically linked `spy` of the
  release archives, and into any host that links the standard layer.
- **Without it**, the source is an ordinary C module that a host links and
  registers with `spy_new_module`.

`make api-reference` generates `spy-module.h` from `spy.h`. Within compatible
releases ([3.4.8](#348-stability)) the table only grows at its end, which
`make check-api` enforces. A library therefore loads into an engine of its
header's series that is as new as the header or newer; any other is refused.

`spy_std_load_native(ctx, name, path)` loads one:

1. It asks the policy about `dlopen`, with `(name, path)`.
2. It opens the library: `dlopen` with `RTLD_NOW | RTLD_LOCAL`, or
   `LoadLibrary`.
3. It finds `spy_module`, and `spy_init_` followed by the last name.
4. It checks the version, hands over the table, and registers the init with
   `spy_new_module`.

Any failure raises `ImportError`, with the system's message or the missing
symbol, worded as CPython's extension loader words it, and closes the
library.

- A loaded library is never closed, since values anywhere in the process may
  hold its functions.
- As for any registered module, the context runs its init on each first
  import. An init that failed runs again on the next import, without
  reopening the library.
- A library holds one table: one that another copy of the engine in the same
  process linked is refused.

The release archives' `spy` for Linux is linked statically, and glibc's
static `dlopen` warns at link time that it needs the C library of the build
at run time. A module loads all the same, since it reaches the engine
through the table and only its own calls reach the system's C library: a
`spy` built on Ubuntu 24.04 (glibc 2.39) was checked importing `fib.so`
built against glibc 2.28, 2.39 and 2.41, each on its own system.

Native code is not sandboxed. It runs in the host's process with the host's
rights, outside the mounts and the policy, and outside the step and memory
budgets, which count only the work and memory it asks of the engine.
Allowing `dlopen` trusts the library completely. Where the platform has no
shared libraries (WebAssembly), `spy_std_load_native` raises `ImportError`.

Programs built with `spyc` do not load shared libraries: they are
self-contained, and native code is compiled into them instead
([Building programs 5.4](build.md#54-native-modules)).

The in-process Go, Rust and Java bindings call `spy_std_load_native` as
`LoadNative`, `load_native` and `loadNative`
([packaging/go.md](packaging/go.md), [rust.md](packaging/rust.md),
[java.md](packaging/java.md)). A library links to the engine copy that
loads it first, so it loads into every runtime of that binding in the
process, and another copy of the engine refuses it. The worker protocol's
`NATIVE` request loads one in the worker before it seals itself
([packaging/protocol.md](packaging/protocol.md) 7.1); the worker packages
send it from `load_native` (Python, Rust), `LoadNative` (Go) and
`loadNative` (Java).

### 3.5 Python binding

The `small-python` package (in `python/`, imported as `small_python`) runs
the engine from CPython 3.10 or later. It links no C into CPython: each
`Runtime` starts a worker process, `spy-worker`, built from `spy-worker.c`,
`spy.c`, and `spy-std.c`, and speaks to it over pipes with the protocol of
[packaging/protocol.md](packaging/protocol.md). An engine crash ends only the
worker and raises `small_python.WorkerError`. The package is specified in
[packaging/python.md](packaging/python.md); its user documentation is
[python/docs](../python/docs/README.md).

```sh
pip install ./python     # or: cd python && uv sync
make test-binding
```

```python
import small_python

with small_python.Runtime(step_limit=1_000_000, memory_limit=64 << 20, timeout=5) as rt:
    @rt.function
    def fetch(key, *, default=None):
        return {"answer": 42}.get(key, default)

    rt.register_module("host", {"fetch": fetch}, source="def twice(n): return n * 2")
    rt.exec("from host import twice")
    print(rt.eval("twice(fetch('answer'))"))  # 84
```

`Runtime(*, std=True, step_limit=0, memory_limit=0, timeout=None,
output=None, loader=None, message_limit=64 << 20)` owns one context in one
worker. A runtime is a context manager.

| Argument | Effect |
| --- | --- |
| `std` | Register the standard layer |
| `memory_limit` | Bound the bytes the engine holds; beyond it, a `MemoryError` stops the operation |
| `timeout` | Bound the seconds one operation runs in the worker; then the worker is terminated and `small_python.Timeout` raised |
| `output` | Receives printed text (default `sys.stdout.write`) |
| `loader` | Maps a module name to source or `None` |

| Method | Effect |
| --- | --- |
| `eval(source, filename)` | The last expression's value |
| `exec` | Run source |
| `call(function_or_global_name, *args, **kwargs)` | Call an engine function |
| `define(name, f)`, the `function` decorator | Give the engine a host function |
| `register_module(name, members, source)` | A module, built on `spy_new_module` |
| `mount(directory, path=None, *, read_only=False)` | Let `open` reach a directory; none is mounted by default |
| `collect`, `close` | Collect cycles; end the worker |
| `rt[name]` | Read, assign, and delete globals |

Values that cross the boundary:

- **By copy:** `None`, `bool`, `int` (any size), `float`, `complex`, `str`,
  `bytes`, `bytearray`, `list`, `tuple`, `dict`, `set`, and `frozenset`. From
  the engine, only exact instances of those types are copied.
- **Python callables** become native functions that keep a reference to the
  callable and receive keyword arguments.
- **Other engine values** come back as `small_python.Object`, a handle the
  worker holds. It forwards calls, attributes, items, `len`, `in`,
  iteration, comparisons, hashing, `repr`, `str`, `dir`, and truth to the
  engine, and stops working once its runtime closes.
- **Other Python objects** are rejected with `TypeError`.

Errors:

- An engine exception reaches Python as `small_python.Error`, with `type`,
  `message`, `exception` (the engine object), `filename`, and `lineno`.
- A Python exception raised by a host function becomes the engine builtin
  exception with the nearest builtin class name in its MRO (else
  `RuntimeError`) and the same `args`. If nothing handles it, it is the
  `__cause__` of the `Error`.
- An `Error` passing back through a host function re-raises its original
  exception.

Host functions cannot call `eval`, `exec`, or `close` on their own runtime;
they may call engine functions they receive. A runtime belongs to one thread
at a time: other threads are refused while it runs.

### 3.6 Rust crates

The crates in `rust/` are specified in
[packaging/rust.md](packaging/rust.md). `small-python-src` carries the C
sources for build scripts; `small-python-sys` compiles `spy.c` and
`spy-std.c` with the `cc` crate and binds `spy.h` by hand; `small-python`
wraps it in a safe API in which every value borrows its runtime, with an
optional `serde` feature; `small-python-worker` compiles and embeds
`spy-worker` and speaks [packaging/protocol.md](packaging/protocol.md) to it,
with the Python package's limits, timeout, and loss rules. Nothing needs to
be installed beyond a C11 compiler; MSVC is not one.

```sh
make test-rust
cd examples/todo && cargo run    # a Flask-style Python application served by axum
```

### 3.7 Go module

The module in `go/` is specified in [packaging/go.md](packaging/go.md).
`spy` compiles `spy.c` and `spy-std.c`, copied beside it by `make
go-vendor`, with cgo, and wraps them in a Go API that converts by reflection
and releases values the garbage collector drops on the runtime's next call;
`worker` runs a `spy-worker` executable and speaks
[packaging/protocol.md](packaging/protocol.md) to it, with the Python
package's limits, timeout, and loss rules.

```sh
make test-go
```

### 3.8 Java artifacts

The Maven build in `java/` is specified in
[packaging/java.md](packaging/java.md). `io.github.soasme:small-python`
compiles `spy.c` and `spy-std.c` with one file of JNI glue, `spy-jni.c`,
into a library its jar carries for each platform, and wraps it in a Java
API that converts records, lists, and maps by reflection and releases
values the garbage collector drops on the interpreter's next call;
`io.github.soasme:small-python-worker` carries `spy-worker` for each
platform and speaks [packaging/protocol.md](packaging/protocol.md) to it,
with the Python package's limits, timeout, and loss rules. The entry point
of both is `Interpreter`, as the Java convention reserves `Runtime` for
`java.lang`.

```sh
make test-java
```

## 4 Internals

### 4.1 Source representation

The lexer handles indentation and produces tokens. A recursive-descent statement
parser and precedence-based expression parser build syntax nodes in a source
unit. Parsing validates the whole unit before execution. Functions retain the
source unit containing their bodies so they can outlive their defining call to
`spy_eval`.

Ordinary execution walks those nodes. Generator functions compile to an
internal instruction array, so their execution can suspend:

- Expressions without yields reuse the evaluator. Expressions containing
  yields keep intermediate operands on an owned heap stack.
- A separate cleanup stack records loops, exception handlers, `finally`
  blocks, and context managers.
- Every instruction borrows its AST node from the retained source unit.

A function body that holds a call and cannot suspend compiles to the same
instructions. A call to such a function from such a body pushes a frame on
the context's call stack, and the same instruction loop continues, so these
calls do not nest on the C stack.

C code that a step calls reaches Python the same way, as Lua's `lua_callk`
lets a C function call Lua. It hands the call to the machine together with
a continuation, a C function and its context, and returns; the machine runs
the call as another frame, then the continuation, which finishes the C
code's work or calls again. `iter()` calls a class's Python `__iter__` so.
Called from C with no machine running, the call is made directly and the
continuation runs after it.

There is no peephole optimizer or stable serialized-program format.

### 4.2 Executable generation

`spyc` emits each module's source bytes as a C array:

- Imported modules are bundled in a table sorted by the names the engine
  probes, behind a generated `SPYModuleLoader` ([build.md](build.md)).
- A small embedding entry point registers the standard modules and the C
  modules the program imports. With `-c`, spyc emits the arrays and the
  loader alone.
- The C compiler, which spyc runs unless `-e` or `-c` asks for the C file,
  links it with `spy.c` or `libspy.a`, and with `spy-std.c` when it imports
  any standard module.

The program still parses source at start-up. Embedding source is not
compiling Python to native code.

### 4.3 Runtime values

Values have a type tag, a reference count, an owning context, and a
type-specific payload:

| Type | Representation |
| --- | --- |
| Integers | A signed 64-bit fast path; arbitrary-precision 32-bit limbs for larger values |
| Floats | C `double` |
| Complex | C11 `double complex`, with explicit component construction |
| Strings | Keep their byte length, so embedded NUL characters are representable |
| Lists, tuples | Growable arrays |
| Dictionaries, sets | Entries in insertion order in one array, with a hash index once they grow past eight entries |
| `None`, booleans, `NotImplemented`, `Ellipsis` | Per-context singletons |

Builtin type objects belong to their context; no process-global mutable
runtime objects are used.

Arithmetic:

- It promotes before overflowing signed C integers.
- Signed division and modulo follow floor semantics. Integer-to-float
  conversion and integer division round to nearest, ties to even.
- Comparisons keep exact integer values.
- Exponentiation supports modular inverses.
- Decimal conversion uses the default 4,300-digit limit, which
  `sys.set_int_max_str_digits` changes per context.

Recursion follows CPython's two limits:

- Python frames (function calls, generator resumption, and module execution)
  count against the per-context recursion limit, 1,000 by default. Exceeding
  it raises "maximum recursion depth exceeded".
- A call from one Python function to another whose body holds a call runs
  on the instruction machine, without growing the C stack. Such recursion is
  bounded by the recursion limit alone.
- Calls that C makes (special methods, host callbacks, trace functions), and
  other recursive C paths in the evaluator, parser, repr, comparison, and
  hashing, check the remaining machine stack against a 4 MiB budget. They
  raise CPython's "Stack overflow" `RecursionError` instead of crashing.

### 4.4 Garbage collection

Ordinary reference release uses an explicit pending list, so freeing a deep
acyclic object graph does not recurse through the C stack. The cycle collector
performs trial deletion:

1. Copy each reference count into a temporary count.
2. Subtract every internal object-to-object reference.
3. Treat remaining positive counts as external roots.
4. Mark values reachable from those roots.
5. Remove dead-to-live references, then free unmarked storage.

All internal value edges participate: defaults, bound methods, exception
roots, iterators, slice components, and suspended generator operands,
environments, delegates, and cleanup records. Dead objects stay allocated
while their edges are inspected. Context teardown can free storage directly,
because it invalidates every value at once.

Finalizers (`__del__`):

- An instance whose class defines `__del__` is not freed when its last
  reference is released, or when the collector finds it unreachable. It is
  queued, kept alive by the queue, and marked as finalized. The queue is
  linked through the values themselves, so queueing never allocates.
- Its `__del__` runs at the next statement boundary, or when the top-level
  program finishes, before any weak-reference callbacks.
- Exceptions raised by `__del__` are discarded, because there is no error
  stream.
- Afterwards the instance is freed, unless the finalizer resurrected it.
  `__del__` never runs twice for the same object.
- A collection collects again after running finalizers, so cyclic garbage
  with `__del__` is freed in the same collection.
- An automatic collection runs at a statement boundary, where queued
  finalizers run, and the finalizers it runs do not start another one. One
  that becomes due while a finalizer runs waits for it to return, so that it
  can run the finalizers it finds and free what they leave.
- A collection whose working memory cannot be allocated does nothing; the
  next one reclaims what it left.
- Context teardown never runs finalizers.

Suspended code:

- A suspended generator or coroutine closes when it is released or
  collected, running its `finally` blocks and `__exit__` methods, as
  CPython's does. If its frame object lives on, the frame keeps the
  generator's storage for its code and line, but to Python the generator is
  gone: its weak references are dead (27.2.4).
- A suspended asynchronous generator is passed to the host's finalizer hook
  when one is installed, and is otherwise closed with `aclose()` (27.5.4).

### 4.5 Calls and scopes

A function holds its definition node, source unit, lexical environment, and
evaluated defaults. Calling it creates an environment with that parent, binds
positional and keyword arguments, and declares local names found in its body.
Reading a declared but unassigned
local raises `UnboundLocalError`. Closures retain their environment; cycles
between definitions and scopes are handled by the collector.

Comprehensions have isolated environments. Their outer iterable is evaluated
in the enclosing scope; assignment-expression targets bind in the containing
scope. Generator expressions retain a stack of loop iterators and resume it
on demand. The collector traces each suspended iterator and environment.

Class bodies use separate namespaces, which are not lexical scopes for method
bodies. Exception handlers retain the active exception across nested handlers
and cleanup. A static symbol pass records local bindings and validates
`global`/`nonlocal` declarations before execution. Captured environments retain
the source units that own their symbol tables. Private identifiers are mangled
in their defining class context; attribute lookup uses the spelling it receives.
Annotations, type parameters, and type aliases are evaluated lazily in
annotation scopes (8.7, 16.6), which read a class body's names through its
`__classdict__` cell.

### 4.6 Repository and toolchain

| Path | Role |
| --- | --- |
| `spy.c`, `spy.h` | Engine and public embedding API |
| `spy-unicode.h`, `tools/build_unicode.py` | Generated Unicode properties and development-only generator |
| `cli.c`, `host.h` | CLI and host stream support |
| `spy-std.c`, `spy-std.h`, `modules/` | Standard layer: the host module `sys` |
| `spyc/` | Standalone program generator: Python sources and its C module `_spyc.c` |
| `tools/bootstrap.sh` | Fetches the previous release's spyc, which builds `bin/spyc` |
| `run-cython.c` | Persistent evaluation driver for upstream doctests |
| `tests/run-spec.c` | Conformance driver: the bare core for spec tests and TLA+ replays |
| `Makefile`, `VERSION`, `Changelog` | Build, installation, version, release history |
| `examples/` | Python and C embedding examples |
| `tests/` | Local checks, upstream pins, fetcher, adapter |
| `bench/` | Lifecycle benchmark and cross-engine comparison programs |
| `docs/manual.md` | Engine manual |
| `intrinsics.py`, `spy-intrinsics.h` | Embedded language-level intrinsic objects; generated header is checked in |
| `docs/standards/3_15.md` | Single-file versioned language target |
| `docs/standards/std.md` | Specification of the standard module `sys` |
| `AGENTS.md` | Architecture, naming, evidence, and code-taste requirements |

The build remains a direct C toolchain with an ordinary Makefile. There is no
runtime package manager, generated application framework, or dependency on a
host Python interpreter. Documentation regeneration is an optional development
task; the checked-in Markdown can be read without installing its conversion
tools.

Validate the checked-in documentation with `make docs`. The standard is
edited by hand; `make tla-coverage` checks that each of its sections is mapped
to the TLA+ models that cover it. `make api-reference` regenerates
[api.md](api.md) from `spy.h`, and `make check-api`, part of `make test`,
checks it (3.4.8).

`make unicode-data` regenerates the checked-in Unicode property table with the
pinned oracle; `make check-unicode` verifies it. Ordinary C builds need neither
the oracle nor the generator. In the tables (whose encoding is credited in
[5](#5-sources-and-licenses)), properties are run lengths with a sparse block
index, case mappings are runs of equal offsets, and decompositions are
single-level and expanded recursively. Character names share leading words with
the preceding name.

## 5 Sources and licenses

The architectural reference is QuickJS commit
`7d1c13c5d8f8c6b32893786ed35cdcebd88194d2`, version `2026-06-04`.
Its core/host/compiler separation, Makefile workflow, manual structure, and
external-suite reporting informed this repository. The Unicode property
encoding and its lookup follow QuickJS's libunicode (`build_prop_table` and
`lre_is_in_table`) under its [MIT license](licenses/quickjs.txt); no other
QuickJS implementation code has been copied into the engine. Native modules
follow QuickJS's shared-library modules in where they load (its libc layer,
here `spy-std.c`) and SQLite's loadable extensions in how they reach the
engine (a table of function pointers handed over at load).

The language standard contains derived Python 3.15.2 documentation under its
original PSF license, with copyright notices and complete license text included
in the single-file standard. Cython downloads retain their upstream Apache 2.0
license and other file-specific notices. The adapter reads the checkout rather
than copying or rewriting its tests. These upstream licenses do not establish
a project-wide license for newly authored engine source.

The generated Unicode 17.0.0 property data retains the
[Unicode License V3](licenses/unicode.txt). Its generator queries the pinned
oracle; the generated table is part of the engine source distribution.
