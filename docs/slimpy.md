# slim.py Python Engine

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
- [4 Internals](#4-internals)
  - [4.1 Source representation](#41-source-representation)
  - [4.2 Executable generation](#42-executable-generation)
  - [4.3 Runtime values](#43-runtime-values)
  - [4.4 Garbage collection](#44-garbage-collection)
  - [4.5 Calls and scopes](#45-calls-and-scopes)
  - [4.6 Repository and toolchain](#46-repository-and-toolchain)
- [5 Sources and licenses](#5-sources-and-licenses)

## 1 Introduction

slim.py is a small, embeddable Python-language engine written in C11. The command
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
- Functions, lexical closures, recursion, control flow, containers, and simple
  host-loaded modules.
- Reference counting with iterative destruction and explicit cycle collection.
- A command-line interpreter and a basic interactive shell.
- C source generation for programs that run without a Python installation or
  the original Python source file.
- Local semantic checks and an adapter that runs unchanged upstream Cython
  pure-Python doctests and reports failures.

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
make install PREFIX=/usr/local DESTDIR=/tmp/slimpy-package
```

Installation places commands in `bin`, the header in `include`, the archive in
`lib`, and this manual in `share/doc/slimpy`. Installing is not required to use
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
usage: spy [-c source | -i | --version | file.py | -]
```

| Option | Effect |
| --- | --- |
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

The initial baseline includes 53 differential programs, 34 error cases, 300
integer expressions, 300 floating-point representations, and 5,000 malformed
source inputs. These are project tests, not the upstream compatibility suite.
The host oracle was Python 3.14.3; it validates shared implemented behavior and
does not establish Python 3.15-specific conformance.

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
static doctests from `.py` modules. Cython's own runner also compiles extension
modules, runs unittest cases, checks compiler diagnostics, and processes
multi-file build tests. Those categories need separate support.

The initial full adapter result was **7 passing and 11,432 failing examples**
from 88 attempted files; 14 other files were adapter-ineligible. Most failures
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

On the initial Apple M2 host, macOS arm64, Apple Clang 17, `-O2`, observed values
were 2.6–3.1 microseconds per lifecycle. The Mach-O `__TEXT` segment was 64 KiB;
the executable file was approximately 88 KB. These measurements apply to the
current subset and are not x86 or full-Python measurements.

## 3 Specifications

### 3.1 Python language support

The target is [SLP-315:2026-draft1](standards/3_15.md). It distinguishes Core
language, Host services, and CPython Extension compatibility. The language
edition, engine release, and upstream test revisions are separate identifiers.

| Area | Implemented subset |
| --- | --- |
| Values | `None`, booleans, signed 64-bit integers, doubles, UTF-8 strings, lists, tuples, dictionaries, ranges, functions, modules |
| Expressions | Arithmetic, bit operations, comparisons/chains, boolean operators, conditionals, calls, indexing |
| Control flow | `if`/`elif`/`else`, `while`, `for`, loop `else`, `break`, `continue`, `return`, `assert`, `pass` |
| Assignment | Single targets, item assignment, selected augmented operators |
| Functions | Positional parameters, recursion, lexical closures, local binding analysis |
| Imports | Simple `import` and `from` statements with optional aliases |
| Builtins | Partial `print`, `len`, `range`, `str`, `repr`, `int`, `float`, `bool`, `list`, `tuple`, `dict`, `abs`, `sum`, `min`, `max`, `all`, `any` |
| Methods | List `append`/`pop`; dictionary `get`/`keys`/`values`/`items` |

Known restrictions include fixed-width integers, incomplete Unicode and escape
handling, rejection of indentation tabs, partial builtin signatures, snapshot
dictionary views, and locale-dependent floating conversion. Overflows raise
`OverflowError`; they do not silently wrap. These restrictions are deviations
from the target standard.

Missing features include classes and object protocols, exception objects and
handlers, generators, coroutines, comprehensions, slicing, unpacking, full call
binding, decorators, annotations, matching, `global`/`nonlocal`, sets, bytes,
complex numbers, f-strings, template strings, package imports, and the new 3.15
language facilities. There is no CPython C API/ABI layer.

### 3.2 Modules

The core accepts a host module-loader callback. The callback returns an owned,
`malloc`-allocated source buffer; the engine frees it after parsing. Each
context caches modules by name. A module is cached before execution to support
simple circular imports. Failed initialization removes that module's cache
entry. Each module has a namespace and `__name__`.

The CLI loader reads `name.py` from the original script directory, or the current
directory for stdin and `-c`. There is no default filesystem loader in an
embedded context. Package search paths, relative names, import hooks, lazy
imports, and extension loading are not implemented.

### 3.3 Standard library and host services

There are no standard-library modules built into the core. Language builtins
are separate from standard-library modules. Core `print` requires an output
callback; imports require a loader. An embedding application opts into those
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
`spy_string`, and `spy_list`. Accessors include `spy_type`, `spy_as_int`,
`spy_as_float`, `spy_as_string`, and `spy_truth`. `spy_repr` returns an owned
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
them. These C error records are not yet Python exception objects or tracebacks.

#### 3.4.5 Evaluation

`spy_eval(ctx, source, filename)` parses and executes source, returning the final
expression value or `None`. `spy_exec` discards that value and returns status.
Both preserve globals between calls. A new top-level evaluation clears the
previous error and resets the step counter. Parsing precedes all execution;
runtime errors do not roll back preceding assignments.

Use `spy_get_global` and `spy_set_global` for host access to global bindings.
Do not recursively call `spy_eval` from a callback on the same context.

#### 3.4.6 Host services and limits

`spy_set_output` installs text output; `spy_set_module_loader` installs module
source loading. Neither service is installed by the core automatically.

`spy_set_step_limit` bounds evaluated nodes and iterator/loop work; zero means
unlimited. It is not a memory or wall-time quota and cannot interrupt native
callbacks. This experimental runtime is not an isolation boundary for untrusted
programs.

#### 3.4.7 Collection

`spy_collect` removes unreachable reference cycles and returns the number of
values collected. Externally retained values are roots. The host schedules
collection at suitable safe points. `spy_live_values` reports the current value
count. Context teardown frees remaining cycles regardless of collection timing.

## 4 Internals

### 4.1 Source representation

The lexer handles indentation and produces tokens. A recursive-descent statement
parser and precedence-based expression parser build syntax nodes in a source
unit. Parsing validates the whole unit before execution. Functions retain the
source unit containing their bodies so they can outlive their defining call to
`spy_eval`.

Execution currently walks those nodes. There is no bytecode VM, peephole
optimizer, or stable serialized-program format. Introducing those later must
preserve the standard's evaluation and error semantics.

### 4.2 Executable generation

`spyc` emits source bytes as a C array and adds a small embedding entry point.
The C compiler links this entry point with `spy.c` or `libspy.a`. The program
still parses source at startup. Imported modules are not bundled. Source
embedding is deliberately described separately from native Python compilation.

### 4.3 Runtime values

Values have a type tag, reference count, owning context, and type-specific
payload. Integers are currently signed 64-bit values and floats use C `double`.
Strings retain byte length so embedded NUL characters are representable. Lists
and tuples use growable arrays; dictionaries use ordered linear entries.

Arithmetic checks integer overflow before executing operations that would
overflow signed C integers. Large integer/float comparisons avoid first rounding
the integer to `double`. This improves the implemented subset but does not
replace the required arbitrary-precision number implementation.

### 4.4 Garbage collection

Ordinary reference release uses an explicit pending list, so freeing a deep
acyclic object graph does not recurse through the C stack. The cycle collector
performs trial deletion:

1. Copy each reference count into a temporary count.
2. Subtract every internal object-to-object reference.
3. Treat remaining positive counts as external roots.
4. Mark values reachable from those roots.
5. Remove dead-to-live references, then free unmarked storage.

All internal value edges, including function/environment references, participate.
Dead objects remain allocated while their edges are inspected. Context teardown
can free storage directly because it invalidates every value at once.

### 4.5 Calls and scopes

A function holds its definition node, source unit, and lexical environment.
Calling it creates an environment with that parent, binds positional arguments,
and declares local names found in its body. Reading a declared but unassigned
local raises `UnboundLocalError`. Closures retain their environment; cycles
between definitions and scopes are handled by the collector.

This is an initial scope implementation. Full `global`/`nonlocal`, class and
annotation scopes, call signatures, exception unwinding, suspension frames, and
introspection remain implementation work.

### 4.6 Repository and toolchain

| Path | Role |
| --- | --- |
| `spy.c`, `spy.h` | Engine and public embedding API |
| `cli.c`, `host.h` | CLI and host stream support |
| `spyc.c` | Standalone C program generator |
| `run-cython.c` | Persistent evaluation driver for upstream doctests |
| `Makefile`, `VERSION`, `Changelog` | Build, installation, version, release history |
| `examples/` | Python and C embedding examples |
| `tests/` | Local checks, upstream pins, fetcher, adapter |
| `bench/` | Lifecycle benchmark |
| `docs/slimpy.md` | Engine manual |
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
