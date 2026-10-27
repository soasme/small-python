# Small Python Engine

Version 0.1.0 — development edition

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

The language target is [SLP-315:2026-draft1](standards/3_15.md), the project's
versioned consolidation of the Python 3.15.0 core-language reference. The current
engine implements a subset of that target. It does **not** claim full Python
3.15 compatibility or a passing CPython/Cython suite.

This manual follows the organization of the
[QuickJS manual](https://bellard.org/quickjs/quickjs.html): usage, specifications,
embedding, and internals. QuickJS is the architectural reference, not the source
of Python semantics or this engine's performance claims.

### 1.1 Main features

- One core C implementation file and one public embedding header.
- Independent runtime contexts with explicit ownership of values.
- Functions with argument binding and closures, basic classes and exceptions,
  iterators, comprehensions, generator functions and delegation, sequence slices,
  and host-loaded modules.
- Reference counting with iterative destruction and explicit cycle collection.
- A command-line interpreter and a basic interactive shell.
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

The outputs are `spy`, `spyc`, and `libspy.a`. No Python installation is needed
to build or run those three artifacts. Python is a development dependency for
test adapters and documentation tools.

Build options are set at the top of the Makefile or on the command line:

```sh
make clean
make CC=clang CONFIG_WERROR=y
make clean
make CONFIG_LTO=y
```

Clean before changing compiler or instrumentation flags. The source language
remains C11; LTO is an optional compiler/linker optimization, not a dependency.

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
./spy examples/hello.py
./spy -c 'print(sum(range(10)))'
```

Generate and compile a standalone program:

```sh
./spyc -o hello.c examples/hello.py
cc -std=c11 -Os -I. hello.c spy.c -lm -o hello
./hello
```

The executable embeds its source and interpreter. It requires neither a Python
installation nor the original `.py` file. It still uses the platform C/math
libraries. Static linking depends on the target platform.

### 2.3 Command-line options

#### 2.3.1 `spy` interpreter

```text
usage: spy [--mount dir]... [-c source | -i | --version | file.py | -]
```

| Option | Effect |
| --- | --- |
| `--mount dir` | Let `open` reach `dir` at its own resolved path; repeatable, and replaces the default mount of the current directory |
| `-c source` | Execute the supplied text |
| `-i` | Start the interactive shell |
| `--version` | Print the engine version |
| `file.py` | Execute a source file |
| `-` or no arguments | Read a complete program from stdin |

The interactive shell keeps global variables between submissions. A blank line
ends a compound statement. It currently uses a small C input loop; multiline
editing, contextual colorization, completion, and a Python-written shell remain
unimplemented. Python command-line compatibility, script arguments, `-m`, and
arbitrary CPython switches are not implemented.

#### 2.3.2 `spyc` program generator

```text
usage: spyc -o program.c input.py
```

`spyc` writes a C translation unit containing source bytes and a small `main`
function. The user invokes the C compiler explicitly. The generator does not
invoke a shell or a compiler internally. It does not bundle imported modules,
produce native code for individual Python functions, or emit bytecode yet.

### 2.4 Local tests

```sh
make test
make sanitize
```

The local suite covers C API ownership, context isolation, error recovery,
closures, reference cycles, deep graph destruction, an execution budget,
malformed source, differential behavior against host CPython, standalone
program generation, and interactive submissions.

The current local suite includes 218 differential programs, 160 error cases, 300
integer expressions, 300 floating-point representations, 300 complex expressions
(420 with the 3.15 oracle), and 5,000 malformed
source inputs. A separate numeric suite covers 1,329 arbitrary-integer,
conversion, modular-power, and rounding expressions. These are project tests,
not the upstream compatibility suite.
A separate range suite checks 768 large-bound, slicing, and reverse-iteration
cases against CPython, including bounds and slice lengths with hundreds of digits.
The comparison matrix checks 1,536 combinations of rich-comparison methods,
subclass priority, reflection, and NotImplemented results, plus 600 slice
comparisons. Mutation checks cover
callbacks that change a list or delete a dictionary key during comparison.
The argument matrix compares 560 binding and diagnostic cases with CPython.
The construction matrix checks 288 allocator and initializer combinations.
The class-creation suite checks 240 C3 inheritance hierarchies and exercises
construction callbacks, descriptor mutation, `super` binding, lexical class
cells, and argument evaluation. The rounding suite compares 5,238 numeric
cases, plus special-method dispatch and argument validation.
`make test-stringsearch` uses the pinned oracle to check 286 literal search
examples derived from upstream `string_tests.py` and 5,600 differential cases.
These examples preserve the upstream expected values; ASCII examples are also
checked as bytes. They do not count as passing whole upstream test methods:
nonliteral calls, loops, fixtures, and subclass checks remain port obligations.
`make test-templates` checks 336 template literals and all 21 malformed sources
from the pinned `test_tstring.py` diagnostic table, preserving its expected
messages. Additional checks cover constructors, raw value retention, iteration,
concatenation, matching, and interpolation suspended by `yield` or `await`.
These checks do not count as passing whole upstream template test modules.
The hashing suite compares 913 numeric and compound hashes, with additional
checks for hash callbacks, failures, collision mutations, dictionary methods,
and Python 3.15 tuple hash caching.
It also checks collection of cycles through defaults, bound methods, iterators,
and suspended generator/coroutine stacks, including operands, async iteration,
async context-manager exits, and pending exceptions. The async ownership checks
also pass UndefinedBehaviorSanitizer with recovery disabled.
`make test-async` checks 120 asynchronous-generator operation/state combinations
against the pinned 3.15 oracle, including reuse, concurrent operations, and
closing during suspension. It does not check finalization warnings.
Semantic checks use the separately built, pinned Python 3.15.0 oracle when
available; set `PYTHON` to choose another development interpreter explicitly.
An older host can differ in diagnostics and representations and is not the
language compatibility target.

`make test-spec` runs the language specification suite in `tests/spec`. Each
test follows one section of the Python 3.15 Language Reference, imports only
`tests/spec/harness.py`, and must pass on the pinned oracle before its result on
spy counts, so the tests depend on the specification rather than on any library.
The `doctests` chapter runs CPython's doctest-based tests through a core-only
runner in the harness, with library-dependent examples rewritten to use only
the language. All 50 tests currently pass.

`make test-tla` model-checks the TLA+ specifications in `tests/tla` with TLC
(fetched by `make tla-tools`; it needs a Java runtime) and replays every
transition of the bounded models on the oracle and on spy. They cover
generator and coroutine methods, try/with control flow and exception context,
name resolution, and object finalization and cycle collection; `SpyGC.tla`
also checks spy's own memory-management algorithm against the language
model step for step. The [README](../tests/tla/README.md) states what these
checks do and do not establish.

For CPython coverage, run `make oracle`, `make cpython-discover`, and
`make cpython-report`. The [CPython coverage report](testing/cpython.md) explains
the complete file inventory, dynamic discovery, framework adaptations, and
remaining coverage gaps. `make test-cpython-doctests` is strict about the current
ports; `make test-cpython` additionally requires closing the full inventory.
Both strict upstream targets currently fail.

`make test-cpython-unittest` passes all 326 cases in nineteen unchanged modules:
decorators, augmented assignments, integer literals, unary operators, keyword-only
arguments, assignment expressions, large expressions, Unicode identifiers, exception
variations, type checks, subclass initialization, UTF-8 source, binary operators,
isinstance/issubclass, containment, exception groups, iterator length hints,
UserDict, and barry_as_FLUFL.
It also checks all 119 executed subtests
against the oracle using the documented test-only framework adapter.
`make test-unicode` checks representations, printability, `chr`/`ord`, and identifier
properties for all 1,114,112 code points, plus 297,124 source/NFKC cases against
the pinned oracle. These checks pass; they do not
establish complete Unicode or unittest compatibility.

On the initial macOS host, both installed AddressSanitizer runtimes hung in
their own initialization before `main`. The UndefinedBehaviorSanitizer run
passed using:

```sh
make SANITIZERS=undefined sanitize
```

Linux CI is configured for AddressSanitizer and UndefinedBehaviorSanitizer. A
configured job is not a claim that it has already run successfully.

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

The pinned Cython checkout contains 102 `.py` and 807 `.pyx` files directly in
`tests/run`, plus build fixtures and support files. The adapter currently covers
static doctests from `.py` modules. `make cython-dynamic-report` additionally
executes unchanged modules in isolated oracle processes to discover runtime
class docstrings and `__test__` groups. Its current result is 367 passing and
11,176 failing examples, with 12 adapter-ineligible files and four discovery
errors; these errors remain failures of the strict coverage gate. Cython's own runner also compiles extension
modules, runs unittest cases, checks compiler diagnostics, and processes
multi-file build tests. Those categories need separate support.

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

On Apple M2, macOS arm64, Apple Clang 17, `-O2`, the recorded run measured 164.60
microseconds of CPU time per lifecycle. The Mach-O `__TEXT` segment was 736 KiB;
the executable file was 794,880 bytes. These measurements apply to the tested
subset. They do not establish x86 performance, full-Python performance, a
worst-case latency bound, or the few-kilobyte size goal.

## 3 Specifications

### 3.1 Python language support

The target is [SLP-315:2026-draft1](standards/3_15.md). It distinguishes Core
language, Host services, and CPython Extension compatibility. The language
edition, engine release, and upstream test revisions are separate identifiers.

| Area | Implemented subset |
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
| Annotations and patterns | Lazy annotations, type parameters, type aliases, structural matching; these implementations remain partial |
| Imports | Multiple/dotted imports, aliases, parenthesized import lists, package/relative imports, star imports, `__import__` hooks |
| Builtins | Partial `print`, `len`, `range`, `str`, `repr`, `ascii`, `format`, `int`, `float`, `complex`, `bytes`, `bytearray`, `bool`, `list`, `tuple`, `dict`, `frozendict`, `set`, `frozenset`, `sorted`, `abs`, `pow`, `divmod`, `round`, `hash`, `bin`, `oct`, `hex`, `sum`, `min`, `max`, `all`, `any`, `iter`, `next`, `map`, `filter`, `zip`, `enumerate`, `reversed`, `ord`, `chr`, `type`, `super`, `isinstance`, `issubclass`, `getattr`, `setattr`, `delattr`, `hasattr`, `callable`, `id`, `slice`, `staticmethod`, `classmethod`, `property`, `dir`, `locals`, `globals` |
| Methods | List `append`, `extend`, `insert`, `pop`, `remove`, `clear`, `copy`, `reverse`, `sort`; list/tuple `count`/`index`; dictionary `get`, `keys`, `values`, `items`, `update`, `copy`, `clear`, `pop`, `popitem`, `setdefault`; str/bytes `startswith`, `endswith`, `find`, `rfind`, `index`, `rindex`, `count`; string `join`, `splitlines`, `isprintable`, `isidentifier`, and positional/named-field `format`; slice `indices`; numeric `conjugate`; integer `bit_length`/`bit_count` |
| Dynamic source | Code objects, three-argument `compile` in `exec`/`eval`/`single` modes, `eval`/`exec` with dictionary globals, mapping locals, and custom builtin dictionaries |

Known restrictions include incomplete Unicode and escape
handling, rejection of indentation tabs, partial builtin signatures,
and locale-dependent floating conversion. Fixed-width host conversions raise
`OverflowError`; they do not silently truncate. These restrictions are deviations
from the target standard.

Syntax exceptions expose message, filename, source line, and position fields.
Their string form includes the basename and line when available. Parser
messages and error spans are still incomplete.

Classes use C3 multiple inheritance, explicit and zero-argument `super`, and
lexical `__class__` cells. Construction calls `__set_name__` on a snapshot of
the namespace, then the inherited `__init_subclass__`, before class decorators.
Plain `__init_subclass__` and `__class_getitem__` functions become class methods.
Three-argument `type()` shares this construction path. Metaclasses support
`__prepare__`, `__new__`, `__init__`, custom `mro()`, and base resolution through
`__mro_entries__`. Class namespace writes and reads honor mapping overrides;
native `type.__new__` accepts dictionaries, frozendicts, and their subclasses. Class metadata includes
`__firstlineno__` and `__static_attributes__`. `__slots__` (a string, an iterable,
or a mapping's keys) become sorted, name-mangled `member_descriptor` attributes;
without a `__dict__` slot or a base with a dictionary, instances refuse new
attributes with CPython's messages, and `__weakref__`/`__dict__` slots, class
variable conflicts, `int`/`bytes` bases, and conflicting slotted bases are
checked. A class's `__name__` and `__qualname__` live outside its `__dict__`;
a class that introduces an instance dictionary or weak references gets the
shared `<attribute '__dict__'>` and `<attribute '__weakref__'>` descriptors in
its `__dict__`, following CPython's rules for builtin bases (`__weakref__` reads
as None). Changing bases, complete class-cell propagation, and some builtin
subclasses remain unsupported. Descriptor
lookup honors data-descriptor precedence and supports `__get__`, `__set__`,
and `__delete__`. Builtin types expose method descriptors and slot wrappers
(`list.append`, `int.__add__`, `object.__repr__`) with CPython reprs and
names; they are created on first lookup and do not change implicit
special-method dispatch. Dictionary `keys`, `values`, and `items` return live
views; keys and items views are set-like, and `mapping` returns a read-only
native C `mappingproxy`. Class `__dict__` also returns a live, read-only proxy.
Proxies forward mapping methods, support generic aliases, and copy an exact
dictionary before comparison with an arbitrary reflected-equality callback,
following Python 3.15. Their implementation no longer uses embedded Python.
Native `frozendict` shares dictionary lookup, views, unpacking, and pattern
matching. Its hash combines stored key hashes with value hashes and caches the
completed result. Exact frozen copies can reuse the original value; subclass
copies produce plain frozen mappings. `eval` and `exec` accept frozen globals
with an existing `__builtins__` entry and reject writes and deletions. Pickle
round trips remain untested because the pickle module is not implemented.
The builtins module provides every CPython 3.15 builtin except `input`,
which needs a host stream, and `help`, `copyright`, `credits`, and
`license`, which come from the `site` module. `open` reaches only host
directories mounted with `spy_mount` (see [Host services and
limits](#346-host-services-and-limits)); without a mount every path raises
`PermissionError`. It returns `_io`-named `FileIO`, `BufferedReader`,
`BufferedWriter`, `BufferedRandom`, and `TextIOWrapper` objects with CPython's
modes, argument validation, reprs, `with`/iteration, `readline`/`readlines`,
`seek`/`tell`/`truncate`, universal and explicit newline handling, and
`UnsupportedOperation` (an `OSError` and `ValueError`). Buffered objects pass
straight through to the descriptor. Text files decode `utf-8` (the 3.15
default), `latin-1`, or `ascii`, the codecs `str.encode` supports; integer
descriptors and `opener` are refused. `OSError(errno, strerror, filename,
winerror, filename2)` follows CPython: the errno selects the subclass, the
attributes are set, a filename shortens `args`, and `str` gives
`[Errno N] message: 'name'`. Exception fields (`args`, the chaining
attributes, and each class's members such as `errno`, `msg`, `value`, or
`name`) are kept outside the instance `__dict__`, as CPython's C members are:
deleting one follows CPython, and `BaseExceptionGroup`'s `message` and
`exceptions` are read-only. A group accepts any sequence and keeps the repr of
a custom one. `__reduce__` and `__setstate__` follow `BaseException`,
`OSError`, `ImportError`, and `AttributeError`. Unicode errors take and expose
`encoding`, `object`, `start`, `end`, and `reason`, and codec failures raise
them with those fields, covering a run of unencodable characters. The class
attributes are `member_descriptor` and `getset_descriptor` objects with
`__get__`, `__set__`, and `__delete__`. `exit` and `quit`
raise `SystemExit` with their code, and `SystemExit.code` follows CPython.
`__build_class__` creates a class as a class statement does, calling an
ordinary function for the body; `__lazy_import__` returns a lazy import object
as the `lazy import` statement does; `breakpoint` calls `sys.breakpointhook`,
raising "lost sys.breakpointhook" when it is absent. Builtin argument counts and
keywords are checked with CPython's messages. `types.FunctionType` creates a
function from a code object, and `exec` and `eval` run a function's code
object as a call with no arguments. A closure for either must consist of cells
bound in the function's defining scopes with the same globals, because spy
functions share their defining environment rather than holding cells.
`compile` accepts `flags`, `dont_inherit`, `optimize`, `module`, and
`_feature_version` with CPython's validation; flags do not change the
resulting code, and `PyCF_ONLY_AST` raises `NotImplementedError`.
Exceptions carry traceback objects as CPython builds them: an error adds an
entry for each frame it passes through, `raise exc` continues `exc`'s
traceback, and a bare `raise` adds none. Entries have `tb_next` (assignable,
with loop detection), `tb_frame`, `tb_lineno` (the statement's line), and
`tb_lasti` (always 0, since there is no bytecode); `__exit__`,
`generator.throw`, `with_traceback`, and `types.TracebackType(...)` accept
and pass them. Exception support still lacks complete chaining and all
builtin-specific constructors.
The 3.15 `sentinel` builtin creates unique named objects (PEP 661) that
record their creating module, copy as themselves, reduce to their name, and
form unions with `|`. `object.__reduce__`, `__reduce_ex__`, and `__getstate__`
follow `typeobject.c`: `__getnewargs_ex__`/`__getnewargs__`, `__dict__` and
slot state, list and dict items, and `copyreg` (imported from the host when
needed) for protocols below 2. Builtin functions expose `__self__`. Functions, bound methods, and builtin
method descriptors expose `__get__`. A builtin base that precedes the defining
class in the MRO supplies its own slot on attribute access, as CPython's type
lookup does, so enum mixins such as `IntFlag` and `StrEnum` resolve their
methods correctly. Setting an
attribute of a builtin object without `__dict__` raises CPython's three
`AttributeError` forms, and unsupported orderings name the operator and types.
`isinstance` and `issubclass` follow `Objects/abstract.c`: exact types check
the MRO, tuples are searched, other targets use `__instancecheck__` or
`__subclasscheck__`, and objects with a tuple `__bases__` act as classes,
with recursion limits on cyclic bases.
`ImportError` accepts `name`, `path`, and `name_from` keywords and keeps a lone
argument as `msg`. `AttributeError` accepts `name` and `obj`, and `NameError`
accepts `name`. Failed attribute lookups and name lookups fill these attributes,
as CPython does.
Exception notes and `add_note` are supported; a failed `__set_name__` callback
retains its exception and receives a note identifying the descriptor and class.
Instance reads, writes, and deletions support `__getattribute__`, `__setattr__`,
and `__delattr__`, with explicit `object` methods for default behavior.
`__getattr__` follows failed reads; implicit special-method lookup bypasses
these interception hooks. Properties receive their class attribute name and
expose writable `__name__` metadata. Custom `__class_getitem__` supports class
subscription; builtin generic aliases and unions use embedded intrinsic objects.
Parenthesized manager lists work for synchronous and asynchronous managers. Builtin type introspection and
signatures are partial; most builtins reject keyword arguments. Bytes support
literals, sequence operations, integer/iterable construction, and string/bytes
method families. Bytearray methods include `resize` and Python 3.15's `take_bytes`; bounds and
storage are rechecked after conversion callbacks. `memoryview` wraps bytes,
bytearrays, other views, and objects with `__buffer__`. It supports native
struct formats (including `e`, `?`, and `P`) and `cast` between 1-D and N-D
shapes. Indexing, slicing, item assignment, comparison, hashing, `tolist`,
`tobytes`, `hex`, `toreadonly`, `release`, and the context-manager protocol
are provided. Bytes consumers accept views. A bytearray with live exports
refuses to resize, and raises CPython's `BufferError`. `bytes` and `bytearray`
expose `__buffer__`. Struct-module formats beyond native single items,
multi-dimensional sub-views, and CPython's allocation introspection remain
unsupported. Encoding and decoding support a limited set of codecs;
the standard-library codec registry is unavailable. Iterator types
are not yet distinguished completely by `type()`. The sequence, dict, set,
range, and reversed iterators provide CPython's `__length_hint__`, and
`list()`, `list.extend`, and `bytearray.extend` propagate errors from a user
iterable's `__len__` or `__length_hint__` as `PyObject_LengthHint` does. Syntax errors for parameter
lists, assignment, deletion, loop, `with`, and keyword-argument targets, `assert`
and condition `=` typos, starred arguments, string prefixes, unbalanced brackets,
missing indented blocks, and conditional expressions follow CPython's lexer and `invalid_*` grammar rules;
errors CPython raises from its compiler (`'break' outside loop`, `'return'
outside function`, misplaced `async for`, `async with`, and `await`) are raised
only after the whole source parses. Some diagnostics still differ from CPython.
These are open compatibility issues, not changes to the standard.
Classes defining `__eq__` without `__hash__` become unhashable. Dictionary/set
entries store hashes and use linear lookup among matching hashes. `hash()` calls
user-defined hash methods, validates their results, and normalizes oversized
integers. Numeric hashes preserve equality across integers, floats, and complex
numbers. Tuples cache successful hashes; slices and ranges are hashable when
their components permit it. String/bytes hashes currently use unsalted FNV-1a;
hash randomization and CPython's hash-seed controls remain unimplemented.
Numeric and compound hash algorithms adapt CPython's implementation under its
[license](licenses/python.txt).

Class factories may return unrelated objects without calling `__init__`.
Returned subclasses use their own initializer. `object.__new__`, `object.__init__`,
and `BaseException.__new__` are available with allocation/type checks. Numeric,
string, sequence, dictionary, and set subclasses retain an underlying builtin
value. CPython's complete allocator-slot restoration behavior is not implemented.

F-strings support expressions, debug fields, conversions, nested format
specifications, raw literals, and generator suspension inside fields. String
`format` and `format_map` follow CPython's parser: automatic and manual
numbering, attribute and index field paths, conversions, nested replacement
fields in specifications (two levels), and CPython's diagnostics. The format-spec
mini-language for `str`, `int`, `bool`, `float`, and `complex` is ported from
CPython: fill code points, alignment, sign, `z`, `#`, zero padding, Unicode
digit widths, `,`/`_` integer and fractional grouping, every presentation type,
the short float repr, and CPython's diagnostics; `n` uses the C locale. Percent
formatting for `str`, `bytes`, and `bytearray` follows CPython's conversions,
flags, `*` widths and precisions, mapping keys, and diagnostics. Unicode escaping, printability, identifier properties, and
`\N{...}` escapes (names and aliases, case-insensitive; Hangul and derived
ideograph names computed) use checked-in Unicode 17.0.0 data. Source identifiers undergo NFKC normalization
before scope analysis and private-name mangling; dynamic string attribute and
keyword names retain their original spelling. Byte sources, CLI files, and imports
honor first/second-line encoding comments and UTF-8 BOMs. Unicode string sources
ignore encoding comments. UTF-8, ASCII, Latin-1 and ISO-8859-15 decoding is native;
other codecs and some decoding diagnostics remain incomplete. CR and CRLF become
LF before parsing, including inside string literals. Indentation uses eight-column
tab stops and checks for inconsistent mixing with spaces. The lexer rejects invalid UTF-8.
String normalization APIs and many other Unicode operations remain incomplete.

Module/class namespaces and explicit execution mappings are live; optimized
function locals are snapshots. Class and execution locals may be arbitrary
mappings. Globals must be dictionaries, including subclasses. Compile flags
remain incomplete. Function code objects expose argument counts, names,
filenames, first-line metadata, and CPython's sorted `co_freevars` and
`co_cellvars` (including names passed through to nested scopes and the
implicit `__class__`). A function's `__closure__` holds cells that read and
write the defining scope's variable; `types.CellType` cells compare by
contents. Execution and replacement of function code objects remain
unsupported; code with free variables is rejected as in CPython. Code objects are cached per parsed definition, so
functions created from the same definition share their code object. `gi_code`,
`cr_code`, and `ag_code` retain that identity after the suspended instance closes.
Code objects retain parsed syntax and internal
generator instructions; there is no public bytecode format. `sorted` and
`list.sort` support stable key sorting and reverse ordering, evaluating each
key once. In-place sorting detects mutation by callbacks and restores the list.

Generator functions preserve operands, loop state, active exceptions, and
pending cleanup across suspension. Explicit `close()` runs cleanup and returns
a generator return value. Automatic finalization on reference release or cycle
collection is not implemented. Live frame objects and some
yield locations (including class bases) remain unsupported. Raise expressions and
explicit causes may yield or await; assertions retain their original message objects.
Lists, tuples, strings, bytes, and ranges support slicing. Range bounds, indices,
steps, and `slice.indices()` lengths use arbitrary-precision integers. Range
iteration, reverse iteration, integer membership, equality, `count`, and `index`
are supported; `len` rejects lengths exceeding the host's supported size.
Slices compare their three components lexicographically, preserving identity
shortcuts and user-defined comparison results.

Coroutines and asynchronous generators share the owned suspension stacks.
Async context-manager exits may suspend during return, loop exits, and exception
handling. Asynchronous-generator operation objects reject concurrent operations
and reuse. Comprehensions share that execution machinery, including nested
async clauses and awaited elements/filters. Generator-based coroutines, automatic async
finalization, unawaited-operation warnings, and frame/code introspection remain
missing. The core does not provide an event loop.

Future statements are checked as CPython's compiler does: they must come
first (after at most a docstring), name a known feature (`braces` is "not a
chance"), and `barry_as_FLUFL` or compile()'s `CO_FUTURE_BARRY_AS_BDFL` flag
makes `<>` the inequality operator. The statement still imports `__future__`
when a host provides it and binds nothing otherwise. Under `from __future__
import annotations` (PEP 563) annotations become strings written as CPython's
AST unparser writes them; functions return them from `__annotate__`, and module
and class bodies store them in an eager `__annotations__` dict. compile(),
exec(), and eval() inherit the running code's future statements unless
`dont_inherit` is true. Compiler-phase
SyntaxErrors from compile(), exec(), and eval() strings have no `text`, as in
CPython.

Instantiating a class whose own `__abstractmethods__` is true raises CPython's
TypeError naming the sorted methods. Source nesting follows CPython's limits:
200 levels of brackets ("too many nested parentheses"), and expressions too
deep for the parser raise MemoryError ("Parser stack overflowed"); prefix
operator runs and long operator chains do not count against the C stack per
operator, and the compiler's checks are bounded by stack use.

Lazy annotations, structural matching, exception groups, generic parameters,
and type aliases have implementations and local checks; their complete upstream
modules have not passed. Memoryview, complete introspection,
lazy imports, and other 3.15 facilities remain missing. There is no CPython C API/ABI layer.

Template strings use C objects with read-only `strings`, `interpolations`, and
`values` attributes. Interpolations retain `value`, `expression`, `conversion`,
and `format_spec`; constructing a template does not call the value's conversion
or formatting methods. Iteration omits empty literal strings. Template and
interpolation types are final and can be obtained with `type(t'')` and
`type(t'{0}'.interpolations[0])` without a library import. The standard-library
`string.templatelib` package, pickle protocols, and complete descriptor
introspection are not supplied by this implementation.

Generic and related intrinsic objects currently use Python source embedded in
`spy-intrinsics.h`, generated from `intrinsics.py` and interpreted by `spy` on
first use. This adds no external dependency or Python build requirement, but it
is a remaining deviation from the requested C11-only implementation of language
semantics. The parser, evaluator, value storage, and collector are C11.

### 3.2 Modules

The core accepts a host module-loader callback. The callback returns an owned,
`malloc`-allocated source buffer; the engine frees it after parsing. Each
context caches modules by name. A module is cached before execution to support
simple circular imports. Failed initialization removes that module's cache
entry. Each source module has a namespace, `__name__`, and `__package__`.
Packages have `__path__`; the current loader does not search its contents.
As in importlib, an import returns the module that `sys.modules` holds once
the source has run, and a submodule that importing its parent placed in
`sys.modules` needs no loading. A module-level `__getattr__` supplies missing
attributes (PEP 562). Failed imports set `ImportError.name`. A missing `from`
name reports the module, its file, and `name_from`, as CPython does.

For `pkg.mod`, the core first requests `pkg.mod.__init__` from the callback,
then `pkg.mod` if no package source exists. The CLI maps dots to directory
separators and reads the resulting `.py` file under the original script
directory, or the current directory for stdin and `-c`. There is no default
filesystem loader in an embedded context. Relative imports use `__package__`.
Import statements honor the frame's builtin `__import__` function; the default
implementation loads sources through the callback. The `builtins` module exposes
the context's builtin namespace directly and needs no loader.

Module specs, namespace packages, configurable package search paths, meta-path
finders, and extension loading remain missing.

Python 3.15 lazy imports (`lazy import`, `lazy from ... import`) bind
`lazy_import` placeholders at module level outside `try` blocks. Reading a
placeholder through a module global, class namespace, or module attribute
calls `__import__` and replaces the binding; a failure is chained to an
ImportError cause naming the lazy import. `from` imports of an already-loaded
module bind the attribute directly. The global lazy-import filter and
`sys.set_lazy_imports` are not provided.

### 3.3 Standard library and host services

The core engine (`spy.c`, `libspy.a`) provides the language and its builtins
but no standard modules. A standard layer, `spy-std.c` (`libspy-std.a`,
declared in `spy-std.h`), plays the role of QuickJS's `quickjs-libc`: its
`spy_std_init` registers `_thread`, `_typing`, `collections`, `gc`,
`itertools`, `sys`, `types`, and `weakref`, with `_weakref` as the primitive
half of `weakref`, and `spy_std_init_module` registers one of them. The `spy`
command, `spyc` programs, and the test drivers link it. The layer uses only the
public API: the modules are Python sources that import their engine primitives
(the weak table, frames, collection, recursion and integer-string limits, the
handled exception, and host output) from `_spy`, a private module every
context has. `print` and interactive display write to `sys.stdout` once a
`sys` module has been imported. `_typing` exposes the engine's
type-parameter, alias, generic, and union objects so the standard library's
`typing` imports. `gc.collect()` runs the cycle collector during execution.
`gc` reports referents and referrers and CPython's tracking rules. Its
enable, disable, threshold, and debug settings are recorded but schedule
nothing. `_thread` describes the engine's single thread. Its locks
keep CPython's states, arguments, and errors. A blocking acquire that only
another thread could satisfy raises `RuntimeError` instead of hanging, and
starting a thread raises `RuntimeError`. Their Python sources live in `modules/` and are embedded into
`spy-std-modules.h`; an import finds them before the host loader, needs no
loader, and parses them only on first use. `collections` provides `deque`,
`defaultdict`, `OrderedDict`, `namedtuple`, `Counter`, `ChainMap`, `UserDict`,
`UserList`, and `UserString` (the last six are CPython's own Python code).
`itertools` provides all of CPython 3.15's iterator types, with its argument
checks and messages; the tee buffer and `_grouper` follow the C module.
`collections` is a package. As in CPython 3.15, `collections.abc` is the
standard library's `_collections_abc`, which the host loader supplies on first
use. `types` names the engine's builtin types and
provides `SimpleNamespace`, `new_class`, `prepare_class`, `resolve_bases`,
`get_original_bases`, and `DynamicClassAttribute`; descriptor-member, and capsule types and `coroutine()` are absent; it names
`CellType`, `FrameType`, `FrameLocalsProxyType`, and `TracebackType`;
`LazyImportType` is the lazy-import placeholder type. `sys` keeps the runtime
state natively: `modules`, `exception()`, the recursion limit, the integer
string-conversion limit, and `stdout`/`stderr` streams that write to the host
output callback (`print()` and interactive display use `sys.stdout` once `sys`
is imported). It also provides `exc_info`, `exit`, `intern`, `displayhook`,
and constant metadata (`version_info`, `float_info`, `int_info`, `hash_info`,
`flags`, `implementation`, whose name is `smallpython`). `_getframe()` returns
frame objects for running calls (functions, generators, class bodies, and
modules) with `f_globals`, `f_locals`, `f_back`, `f_code`, `f_lineno`,
`f_builtins`, and `f_generator`; a function frame's `f_locals` is a
write-through `FrameLocalsProxy` as in PEP 667. Line numbers are those of the
executing statement. `_getframemodulename()` is provided. Tracing, profiling,
`f_lasti`, `frame.clear()`, reference counts, audit hooks, and a separate
error stream are not provided. `_weakref` re-exports the `weakref` primitives
for the standard library's pure-Python modules.
`weakref` provides `ref`, `proxy`, `getweakrefcount`, `getweakrefs`,
`WeakMethod`, `WeakValueDictionary`, `WeakKeyDictionary`, `WeakSet`, and
`finalize` (which has no interpreter-exit hook).

Weak references use a per-context table of borrowed (referent, reference)
pairs. Instances of classes without `__slots__` (or with `__weakref__` in
them), classes, functions, bound methods, builtin functions, sets, frozensets,
generators, coroutines, code objects, and modules are weakly referenceable,
as in CPython. Releasing a referent, or collecting it in a cycle, clears its
references and queues their callbacks, which run at the next statement
boundary; callback exceptions are discarded because there is no error stream.
Closures retain their whole defining environment, so a closure can keep alive
a local that CPython would have released.

Other standard-library modules are not built in. The `builtins` module exposes
language builtins. Core `print` requires an output callback; other source
imports require a loader. An embedding application opts into those
capabilities. Optional Python-level C library wrappers remain future work.

Removing standard-library dependencies does not remove requirements for
classes, exceptions, Unicode, imports, or async syntax. The specification keeps
those requirements in the Core profile and treats unavailable host services
separately.

### 3.4 C API

#### 3.4.1 Contexts

`spy_context_new()` returns an independent context or `NULL` on allocation
failure. `spy_context_free()` destroys it and all remaining values. Contexts
have no process-global mutable runtime state. Use independent contexts on
different threads; do not concurrently enter one context.
`spy_set_opaque` and `spy_get_opaque` attach one host pointer to a context,
like `JS_SetContextOpaque`, so callbacks such as a module init can find the
host object that owns the context.

The current API does not separate a shared allocator/runtime from execution
contexts as QuickJS does. One `SPYContext` owns its heap, globals, module cache,
errors, callbacks, and execution budget.

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

`spy_eval(ctx, source, filename)` parses and executes source, returning the final
expression value or `None`. `spy_exec` discards that value and returns status.
`spy_eval_interactive` also displays each non-`None` expression through the
output callback, including expressions inside interactive loops and conditionals.
Function and class bodies retain ordinary execution behavior. Successful display
updates the builtin `_` binding. All three entry points preserve globals between calls. A new top-level evaluation clears the
previous error and resets the step counter. Parsing precedes all execution;
runtime errors do not roll back preceding assignments.

Use `spy_get_global` and `spy_set_global` for host access to global bindings.
Do not recursively call `spy_eval` from a callback on the same context.

#### 3.4.6 Host services and limits

`spy_set_output` installs text output; `spy_set_module_loader` installs module
source loading. Neither service is installed by the core automatically.

`spy_mount(ctx, directory, path, flags)` lets `open` reach a host directory
at an absolute guest path, or at the directory's own resolved path when
`path` is `NULL`; `SPY_MOUNT_READ_ONLY` refuses writes with `EROFS`. Nothing
else is reachable: a guest path is normalized lexically, must fall inside a
mount (the longest matching one), and is then resolved on the host with
`realpath`, so `..` and symbolic links cannot leave the mount, and files are
opened with `O_NOFOLLOW`. Relative paths start at the first mount. The context
owns every descriptor `open` creates and closes the rest when it is freed;
other descriptors, such as the process's standard streams, are unreachable.
The `spy` command mounts its working directory at its own path. File access
needs a POSIX host; elsewhere `spy_mount` and `open` raise `OSError`.

`spy_new_module(ctx, name, init)` registers a module the way QuickJS's
`JS_NewCModule` does. An import finds it before the loader. The first import
creates the module object with `__name__`, `__package__`, and `__builtins__`
set and calls `init(ctx, module)`, which fills it (with `spy_set_attr`,
`spy_native` values, or Python source through `spy_exec_module`) and returns 0,
or -1 with an error set to fail the import. An init that sets `__path__` makes
a package, whose submodules register under dotted names.
`spy_set_flush` optionally supplies a flush callback using the output callback's
data pointer. Otherwise output is treated as unbuffered. Replacing the output
callback clears the flush callback. `print(file=...)` uses the Python object's
`write` and `flush` methods.
`spy_set_input` installs the line reader behind `input()`: it returns a
malloc-allocated UTF-8 line, with or without its line ending, or NULL at the
end of input. Without a reader, `input()` raises `EOFError`; the `spy` command
reads standard input.

`spy_set_step_limit` bounds evaluated nodes and iterator/loop work; zero means
unlimited. It is not a memory or wall-time quota and cannot interrupt native
callbacks. This experimental runtime is not an isolation boundary for untrusted
programs.

#### 3.4.7 Collection

`spy_collect` removes unreachable reference cycles and returns the number of
values collected. Externally retained values are roots. The host schedules
collection at suitable safe points. `spy_live_values` reports the current value
count. Context teardown frees remaining cycles regardless of collection timing.

### 3.5 Python binding

The `smallpython` package (`python/smallpython`) embeds the engine in CPython
3.13 or later as the extension module `smallpython._core`, compiled from
`spy.c`, `spy-std.c`, and the binding. It lets Python programs run Small
Python code and inject Python functions as host functions.

```sh
pip install .            # or: python3 setup.py build_ext --inplace
make test-binding
```

```python
import smallpython

with smallpython.Runtime(step_limit=1_000_000) as rt:
    @rt.function
    def fetch(key, *, default=None):
        return {"answer": 42}.get(key, default)

    rt.register_module("host", {"fetch": fetch}, source="def twice(n): return n * 2")
    rt.exec("from host import twice")
    print(rt.eval("twice(fetch('answer'))"))  # 84
```

`Runtime(*, std=True, step_limit=0, output=None, loader=None)` owns one
context. `std` registers the standard layer; `output` receives printed text
(default `sys.stdout.write`); `loader` maps a module name to source or `None`.
Its methods are `eval(source, filename)` (the last expression's value),
`exec`, `call(function_or_global_name, *args, **kwargs)`, `define(name, f)`
and the `function` decorator, `register_module(name, members, source)` (built
on `spy_new_module`), `mount(directory, path=None, *, read_only=False)` (no
directory is mounted by default), `collect`, and `close`; `rt[name]` reads, assigns, and
deletes globals. A runtime is a context manager.

Values cross the boundary by copy when they are `None`, `bool`, `int`
(any size), `float`, `complex`, `str`, `bytes`, `bytearray`, `list`, `tuple`,
`dict`, `set`, or `frozenset`. Python callables become native functions that
keep a reference to the callable and receive keyword arguments; other engine
values come back as `smallpython.Object`, which forwards calls, attributes,
items, iteration, `repr`, `str`, and truth to the engine and stops working once
its runtime closes. Other Python objects are rejected with `TypeError`.

An engine exception reaches Python as `smallpython.Error` with `type`,
`message`, `exception` (the engine object), `filename`, and `lineno`. A Python
exception raised by a host function becomes the engine builtin exception with
the nearest class name in its MRO (else `RuntimeError`) and the same `args`;
an `Error` passing back through a host function re-raises its original
exception. Host functions cannot call `eval`, `exec`, or `close` on their own
runtime; they may call engine functions they receive. One runtime must not be
used from two threads at once.

## 4 Internals

### 4.1 Source representation

The lexer handles indentation and produces tokens. A recursive-descent statement
parser and precedence-based expression parser build syntax nodes in a source
unit. Parsing validates the whole unit before execution. Functions retain the
source unit containing their bodies so they can outlive their defining call to
`spy_eval`.

Ordinary execution walks those nodes. Generator functions compile to an
internal instruction array so their execution can suspend. Expressions without
yields reuse the evaluator; expressions containing yields preserve intermediate
operands on an owned heap stack. A separate cleanup stack records loops,
exception handlers, `finally` blocks, and context managers. Every instruction
borrows its AST node from the retained source unit. There is no peephole
optimizer or stable serialized-program format.

### 4.2 Executable generation

`spyc` emits source bytes as a C array and adds a small embedding entry point.
The C compiler links this entry point with `spy.c` or `libspy.a`. The program
still parses source at startup. Imported modules are not bundled. Source
embedding is deliberately described separately from native Python compilation.

### 4.3 Runtime values

Values have a type tag, reference count, owning context, and type-specific
payload. Integers use a signed 64-bit fast path with arbitrary-precision
32-bit limbs for larger values. Floats use C `double`, and
complex values use C11 `double complex` with explicit component construction.
Strings retain byte length so embedded NUL characters are representable. Lists
and tuples use growable arrays; dictionaries and sets use linear entries.
`None`, booleans, `NotImplemented`, and `Ellipsis` are per-context singletons. Builtin type objects belong to
their context; no process-global mutable runtime objects are used.

Arithmetic promotes before overflowing signed C integers. Signed division and
modulo follow floor semantics; integer-to-float and integer division use
round-to-nearest-even. Comparisons preserve exact integer values. Exponentiation
supports modular inverses. Decimal conversion currently uses the default
4,300-digit limit, which `sys.set_int_max_str_digits` changes per context.

Recursion follows CPython's two limits. Python frames (function calls,
generator resumption, and module execution) count against the per-context
recursion limit, 1,000 by default, and exceeding it raises "maximum recursion
depth exceeded". Recursive C paths in the evaluator, parser, repr, comparison,
and hashing check the remaining machine stack against a 4 MiB budget and raise
CPython's "Stack overflow" RecursionError instead of crashing.

### 4.4 Garbage collection

Ordinary reference release uses an explicit pending list, so freeing a deep
acyclic object graph does not recurse through the C stack. The cycle collector
performs trial deletion:

1. Copy each reference count into a temporary count.
2. Subtract every internal object-to-object reference.
3. Treat remaining positive counts as external roots.
4. Mark values reachable from those roots.
5. Remove dead-to-live references, then free unmarked storage.

All internal value edges, including defaults, bound methods, exception roots,
iterators, slice components, and suspended generator operands, environments,
delegates, and cleanup records, participate.
Dead objects remain allocated while their edges are inspected. Context teardown
can free storage directly because it invalidates every value at once.
An instance whose class defines `__del__` is not freed when its last reference
is released or when the collector finds it unreachable. Instead it is queued,
kept alive by the queue, and marked as finalized. Its `__del__` runs at the next
statement boundary or when the top-level program finishes, before any weak
reference callbacks. Exceptions raised by `__del__` are discarded, because there
is no error stream. Afterwards the instance is freed unless the finalizer
resurrected it, and `__del__` never runs twice for the same object.
`gc.collect()` collects again after running finalizers, so cyclic garbage with
`__del__` is freed in the same call. Context teardown never runs finalizers.
Automatic generator closing is not implemented; callers must explicitly close
generators whose cleanup must run.

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
Annotation scopes and complete introspection remain work.

### 4.6 Repository and toolchain

| Path | Role |
| --- | --- |
| `spy.c`, `spy.h` | Engine and public embedding API |
| `spy-unicode.h`, `tools/build_unicode.py` | Generated Unicode properties and development-only generator |
| `cli.c`, `host.h` | CLI and host stream support |
| `spyc.c` | Standalone C program generator |
| `run-cython.c` | Persistent evaluation driver for upstream doctests |
| `Makefile`, `VERSION`, `Changelog` | Build, installation, version, release history |
| `examples/` | Python and C embedding examples |
| `tests/` | Local checks, upstream pins, fetcher, adapter |
| `bench/` | Lifecycle benchmark |
| `docs/smallpython.md` | Engine manual |
| `intrinsics.py`, `spy-intrinsics.h` | Embedded language-level intrinsic objects; generated header is checked in |
| `docs/standards/3_15.md` | Single-file versioned language target |
| `tools/build_standard.py` | Reproducible consolidation of pinned Python reference sources |
| `AGENTS.md` | Architecture, naming, evidence, and code-taste requirements |

The build remains a direct C toolchain with an ordinary Makefile. There is no
runtime package manager, generated application framework, or dependency on a
host Python interpreter. Documentation regeneration is an optional development
task; the checked-in Markdown can be read without installing its conversion
tools.

Validate the checked-in documentation with `make docs`. After `make upstream`,
`make standard` regenerates the language reference and `make check-standard`
checks that regeneration is identical. These two optional targets use `uv`
with pinned Pandoc and Pygments packages. They are not part of `make all` or
required for an embedding build.

`make unicode-data` regenerates the checked-in Unicode property table with the
pinned oracle; `make check-unicode` verifies it. Ordinary C builds need neither
the oracle nor the generator.

## 5 Sources and licenses

The architectural reference is QuickJS commit
`7d1c13c5d8f8c6b32893786ed35cdcebd88194d2`, version `2026-06-04`.
Its core/host/compiler separation, Makefile workflow, manual structure, and
external-suite reporting informed this repository. QuickJS implementation code
has not been copied into the engine.

The language standard contains derived Python 3.15.0 documentation under its
original PSF license, with copyright notices and complete license text included
in the single-file standard. Cython downloads retain their upstream Apache 2.0
license and other file-specific notices. The adapter reads the checkout rather
than copying or rewriting its tests. These upstream licenses do not establish
a project-wide license for newly authored engine source.

The generated Unicode 17.0.0 property data retains the
[Unicode License V3](licenses/unicode.txt). Its generator queries the pinned
oracle; the generated table is part of the engine source distribution.
