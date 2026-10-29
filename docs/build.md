# Building programs with `spyc`

> **Status: work in progress.** This document specifies the bundler that
> `spyc` will become. None of it beyond the existing `-c` and `-M` options is
> implemented yet. The formal model (`tests/tla/SpyBuild.tla`) and the build
> tests (`tests/build`) are written ahead of the implementation; until it
> lands, `make test-build` fails.

## Table of Contents

- [1 Introduction](#1-introduction)
- [2 Usage](#2-usage)
- [3 Module resolution](#3-module-resolution)
- [4 Dynamic imports](#4-dynamic-imports)
- [5 The generated C file](#5-the-generated-c-file)
- [6 Source transforms](#6-source-transforms)
- [7 Build metadata and diagnostics](#7-build-metadata-and-diagnostics)
- [8 esbuild feature map](#8-esbuild-feature-map)
- [9 Implementation](#9-implementation)
- [10 Verification](#10-verification)

## 1 Introduction

`spyc` turns a Python program into one C translation unit. Today it embeds a
single source file. The bundler follows the program's imports, as
[esbuild](https://esbuild.github.io/) follows a JavaScript program's, and
embeds every module the program reaches. The program then runs without any
Python file at run time.

Bundling must not change what the program does. esbuild hoists every module
into one scope. Python modules are objects that a program can see in
`sys.modules`, in a cycle, through `__name__` and `__file__`, or by importing
lazily. So spyc keeps each module separate. It embeds the source of each one,
and a generated module loader returns that source when the engine asks for it.
The import system is the same one that runs unbundled programs: modules are
cached, run once, imported parent first, and initialized lazily. A bundled
program only gets its sources from the C file instead of from disk.

This is the QuickJS arrangement: `qjsc` compiles a program and the modules it
imports, `-D` adds modules that only a dynamic import reaches, and `-M`
registers native modules. spyc keeps those three ideas. From esbuild it takes
the command-line features that fit a Python program, as
[section 8](#8-esbuild-feature-map) lists.

### 1.1 Goals

- One `.c` file for a program and all its modules. It needs only `libspy.a`,
  plus `libspy-std.a` when `-M` names a standard module.
- Import semantics identical to the unbundled program run by the pinned
  CPython 3.15 with the same search path: the same modules found, the same
  failures, and the same `__name__`, `__package__`, and `__path__`. The engine
  derives `__file__` from the module name, so `__file__` is the module's
  path relative to its search root, as it is under `spy` (CPython gives the
  absolute path).
- A failed build for a missing module. A build that succeeds does not hide a
  missing module that only fails at run time, except where the program itself
  handles the `ImportError` ([3.4](#34-guarded-imports)).
- Reproducible output: the same inputs give the same bytes, whatever the
  working directory, the absolute paths, or the order of discovery.
- No new engine API. The bundle is a `SPYModuleLoader`.

### 1.2 Non-goals

- Native compilation of Python code. spyc embeds source, and the engine parses
  each module when it is first imported, as it does without a bundle.
- Statement-level tree shaking, identifier mangling, and constant `define`s.
  [Section 8](#8-esbuild-feature-map) explains why each would change behavior.
- Watch mode, a development server, and plugins. `make` with the dependency
  file of [7.2](#72-dependency-file) is the rebuild loop.

## 2 Usage

```text
usage: spyc [options] -o program.c (entry.py | -m module)
       spyc -c [options] -o modules.c (entry.py | -m module)...
```

```sh
spyc -o app.c app.py                      # app.py and everything it imports
cc -O2 -I. app.c libspy.a -lm -o app

spyc -I lib -x raylib -c -o game_py.c game.py   # for a host that registers raylib
spyc -D plugins.* -o app.c app.py               # plus every module of plugins
spyc -O --minify --metafile app.json -o app.c app.py
```

### 2.1 Options

| Option | Meaning |
| --- | --- |
| `-o FILE` | The C file to write. It may not be an input. |
| `-c` | Write only the embedded sources and the loader, for a host's own `main` ([5.2](#52-library-output--c)). Several entries are allowed. |
| `-m MODULE` | Run `MODULE` as `__main__`, as `python -m` does. |
| `-M MODULE` | Register a standard module (`spy-std.c`), as today. Imports of it are not bundled. |
| `-I DIR` | Add a search root after the entry's. May be repeated. |
| `-x MODULE` | External: leave `MODULE` and its submodules out of the bundle. The host provides them at run time. |
| `-D MODULE` | Include `MODULE` even if no import names it. `-D PKG.*` includes every module under package `PKG`. |
| `-N NAME` | Name the `-c` loader `NAME_load`, as `qjsc -N` names its output. The default `NAME` is `spy_` followed by the first entry's name. |
| `--alias NAME=TARGET` | Resolve module `NAME`, and `NAME.sub`, to `TARGET`'s files. |
| `-O`, `-OO` | Python's optimization levels: remove `assert` and set `__debug__` false, and with `-OO` remove docstrings ([6.1](#61-optimization-levels--o-and--oo)). |
| `--minify` | Remove comments and needless spaces, keeping every line number ([6.2](#62-minification)). |
| `--metafile FILE` | Write a JSON description of the inputs and output ([7.1](#71-metafile)). |
| `--deps FILE` | Write a make dependency rule ([7.2](#72-dependency-file)). |
| `--analyze` | Print each bundled module's size to stderr. |
| `-Werror` | Treat warnings as errors. |

spyc exits with 0 on success, 1 when the build fails, and 2 for a usage
error. It writes the output only on success.

### 2.2 Entry points

A file entry runs as `__main__` with `__file__` set to its file name, as
`spy file.py` runs it. It has no `__package__`, so a relative import in it is
an error, as it is in CPython. Its directory is the first search root, as
CPython puts the script's directory first in `sys.path`.

A module entry (`-m pkg.tool`) runs the module's source as `__main__` with
`__package__` set to `pkg`, so its relative imports work. Its first search
root is the current directory, as `python -m` uses. If `pkg.tool` is a
package, its `__main__` submodule runs instead. Its parent packages are
imported first, as `python -m` imports them.

The program may also import its entry by name, `import app`. That runs a
second module, `app`, apart from `__main__`, as it does in CPython.

## 3 Module resolution

### 3.1 Search roots

The roots are, in order: the entry's root ([2.2](#22-entry-points)), then
each `-I` directory in the order given. They play the part of `sys.path`, and
the search follows CPython's path finder (`importlib._bootstrap_external`'s
`PathFinder` and `FileFinder`) exactly.

FindModule(*name*) for a dotted name *name* = *parent*.*tail*, or a top-level
*tail*:

1. If *name* is under an external prefix (`-x`), return External.
2. If *name* was registered with `-M`, return Registered. A registered module
   shadows files of the same name, as CPython's built-in modules do.
3. If *name* is top-level, let *locations* be the roots. Otherwise let *p* be
   FindModule(*parent*). If *p* is not a package, return NotFound. Let
   *locations* be *p*'s locations.
4. Let *portions* be an empty list. For each directory *d* of *locations*, in
   order:
   1. If *d* has a directory entry *tail* and *d*/*tail*/`__init__.py` is a
      file, return Package(*d*/*tail*/`__init__.py`, locations « *d*/*tail* »).
   2. If *d*/*tail*`.py` is a file, return Module(*d*/*tail*`.py`).
   3. If *d*/*tail* is a directory, append it to *portions*.
5. If *portions* is not empty, return Namespace(locations *portions*).
6. Return NotFound.

Three consequences matter in practice. First, a regular package's submodules
are found only in its own directory. A `pkg/extra.py` under a later root is
not `pkg.extra` when an earlier root has `pkg/__init__.py`. Second, a
namespace package (PEP 420) gathers its portions from every root. Third, a
package directory hides a module file of the same name in the same root, but
a namespace directory does not.

Names compare by exact spelling, as CPython's finder compares directory
listings. `import mod` does not find `Mod.py` on a case-insensitive file
system. Only directory entries that are valid identifiers can name modules.
Symbolic links are followed. The module keeps the name it was imported by.

`--alias NAME=TARGET` replaces the leading component(s) `NAME` with `TARGET`
before step 3, so `NAME` and `NAME.x` load the files of `TARGET` and
`TARGET.x`. The module is still called `NAME`, and its `__file__` follows its
name. An alias is the build-time way to swap one implementation for another,
which esbuild users do with `alias` and `define`.

### 3.2 Discovery

The bundle is the smallest set of modules that contains:

1. the entry, and its parent packages for `-m`;
2. each module named by `-D`, and each module found under a `-D PKG.*`;
3. for each module in the set, its parent package;
4. for each source module in the set, every module its imports name
   ([3.3](#33-imports-a-module-names)).

Registered and external modules are never in the set, and spyc does not read
their files. The set is independent of the order spyc visits modules in. The
resolution model (`SpyBuild.tla`) checks this ([10.1](#101-tla-model)).

### 3.3 Imports a module names

spyc parses each module with the engine's own parser
([9](#9-implementation)), so the build accepts exactly the grammar the program
runs with. A syntax error fails the build with the engine's message. It then
walks the whole module, including function bodies, class bodies, and
branches that may never run, because Python imports can run anywhere:

| Source | Names resolved |
| --- | --- |
| `import a.b.c`, `import a.b as x` | `a`, `a.b`, `a.b.c` |
| `from a.b import c` | `a`, `a.b`, and `a.b.c` if it is a module |
| `from . import c`, `from ..x import c` | the package by PEP 328's rules, then `c` if it is a module |
| `from a import *` | `a`, and each name in a literal `__all__` of `a` that is a module |
| `lazy import a`, `lazy from a import b` (PEP 810) | as without `lazy`; the module still runs only on first use |
| `__import__("a.b")`, `__import__("a", fromlist=("b",))` with string literals | as the matching statement |
| `__import__(expression)` | nothing; a warning ([4](#4-dynamic-imports)) |
| `from __future__ import x` | nothing; it is a compiler directive |

A relative import resolves against the importing module's package: the module
itself if it is a package, and otherwise its parent. A file entry has no
package. The errors are CPython's: `attempted relative import with no known
parent package` and `attempted relative import beyond top-level package`.

The names after `from a import` are not always modules. When `a.c` does not
resolve, `c` is taken to be an attribute and nothing is reported. If the
attribute does not exist either, the program fails at run time with the same
`ImportError` it would get unbundled.

spyc cannot see a program that changes `__path__`, `__package__`, or
`__name__`, or that installs import hooks through `__import__` or
`builtins`. Such a program needs `-D` for the modules it reaches that way.

### 3.4 Guarded imports

A missing module fails the build. A program can still have optional
dependencies:

```python
try:
    import fast_codec as codec
except ImportError:
    import slow_codec as codec
```

An import is *guarded* if it appears in the body of a `try` statement that
has a bare `except:`, or a handler naming `ImportError`, `ModuleNotFoundError`,
`Exception`, or `BaseException`, alone or in a tuple. A guarded import that
does not resolve is left out without an error. At run time it raises
`ModuleNotFoundError`, which the handler catches, as it would unbundled. The
metafile records it as missing. An import counts as guarded only where it
appears lexically inside the `try` body. A guard in a calling function does
not count. This is esbuild's rule for `require()` inside `try`.

## 4 Dynamic imports

A computed `__import__(name)` (or `importlib.import_module(name)` in a host
that provides `importlib`) cannot be followed. spyc warns at its line. The
program must then name what it may load with `-D`, as `qjsc -D` names the
modules a JavaScript `import()` may load:

```sh
spyc -D plugins.csv -D plugins.json -o app.c app.py   # these two
spyc -D 'plugins.*' -o app.c app.py                   # every module under plugins
```

`-D PKG.*` includes every module and package found under `PKG`, at any
depth, by listing *PKG*'s locations. It does not include namespace
directories that contain no module. A module named by `-D` must resolve,
otherwise the build fails. Each included module's own imports are followed
like any other.

Whatever is not in the bundle is asked of the host's loader. A standalone
program has none, so the import fails. A `-c` host can chain its own loader
after the bundle's ([5.2](#52-library-output--c)), which is how a program
loads modules from disk next to its embedded ones.

## 5 The generated C file

### 5.1 The module table

The bundle is a table sorted by key, one entry per module, keyed by the
names the engine asks its `SPYModuleLoader` for (`spy.h`):

| Module | Key | Value |
| --- | --- | --- |
| package `pkg` | `pkg.__init__` | the source of `pkg/__init__.py` |
| module `pkg.sub` | `pkg.sub` | the source of `pkg/sub.py` |
| namespace package `ns` | `ns.__namespace__` | empty |

The engine probes `NAME.__init__`, then `NAME`, then `NAME.__namespace__`,
and so the bundle answers each probe exactly as the file system did when
spyc built it. Sources are embedded byte for byte (or as transformed by
[section 6](#6-source-transforms)), with their encoding declarations, so the
engine decodes them as it decodes files.

```c
/* Generated by spyc. Link with libspy.a and the C math library. */
#include "spy.h"
#include <stdlib.h>
#include <string.h>

static const char m0[] = {...};    /* app.py, the entry */
static const char m1[] = {...};    /* pkg/__init__.py */
static const char m2[] = {...};    /* pkg/sub.py */
static const struct { const char *name, *source; size_t size; } modules[] = {
    {"ns.__namespace__", "", 0},
    {"pkg.__init__", m1, sizeof m1 - 1},
    {"pkg.sub", m2, sizeof m2 - 1},
};
static char *load(void *data, const char *name) { /* binary search, malloc copy */ }
int main(void) {
    /* spy_context_new, the -M modules, output callbacks, as today */
    spy_set_module_loader(c, load, NULL);
    /* __file__ = "app.py"; spy_exec(c, m0, "app.py"); report errors */
}
```

The standalone `main` is the current one, with the loader added and the
entry's real file name in place of `<embedded>`. An entry that the program
also imports by name has a table entry that points at the entry's array, so
its source is embedded once.

### 5.2 Library output (`-c`)

With `-c`, spyc writes no `main`. For each entry it writes the source array
it writes today, named after the entry. It also writes one loader for all of
them:

```c
const char spy_game[] = {...};                   /* game.py */
const char spy_level[] = {...};                  /* level.py, a second entry */
char *spy_game_load(void *data, const char *name);  /* a SPYModuleLoader; data is unused */
```

The host installs the loader and runs an entry:

```c
spy_new_module(c, "raylib", raylib_init);        /* the externals it provides */
spy_set_module_loader(c, spy_game_load, NULL);
spy_exec(c, spy_game, "game.py");
```

To load more modules from disk, the host's own loader calls `spy_game_load`
first and falls back to its own search. Several entries share one table, and
a module that two entries import is embedded once. This is what esbuild's
code splitting gives, and in C it costs nothing more.

## 6 Source transforms

The transforms never change a line number. A traceback, `co_lines()`, a
`SyntaxError`, and a `frame.f_lineno` report the original lines, so a
bundle needs no source map. Column offsets may differ after `--minify`.

### 6.1 Optimization levels (`-O` and `-OO`)

`-O` gives the program what `python -O` gives it:

- Every `assert` statement becomes `pass`. A statement spanning several lines
  becomes `pass` followed by the same number of line breaks.
- Every load of the name `__debug__` becomes `False`, including inside
  f-string and t-string fields.

`-OO` also removes docstrings. A module's, class's, or function's docstring
statement is deleted, with its `;` if one follows, so `__doc__` is `None`. If
the docstring is the only statement of a function or class body, it becomes
`pass`. A module docstring before `from __future__ import` is deleted, not
replaced, so the future import stays first.

`sys.flags` is not changed, because it belongs to the host's `sys` module.

### 6.2 Minification

`--minify` rewrites each module's tokens:

- Comments are removed, except a `#!` line, an encoding declaration, and
  comments containing `@license` or `@preserve`. esbuild keeps legal comments
  the same way.
- Each indentation level becomes one space. Trailing spaces are removed.
- Inside a line, a space remains only where two tokens would otherwise merge
  (two names, keywords or numbers, a number followed by `.`) or where the
  tokenizer requires one.
- Line breaks, including empty lines and backslash continuations, stay.
- String, bytes, f-string, and t-string literals stay byte for byte, as do
  docstrings (unless `-OO`).

The result must tokenize to the same tokens, each on its original line. spyc
checks this by tokenizing the result again and fails the build if it does not
hold. Identifiers are never renamed ([8](#8-esbuild-feature-map)).

## 7 Build metadata and diagnostics

### 7.1 Metafile

`--metafile FILE` writes esbuild's metafile shape, with paths relative to the
working directory:

```json
{
  "inputs": {
    "app.py": {"bytes": 412, "imports": [
      {"path": "pkg/__init__.py", "kind": "import-statement", "original": "pkg.sub"},
      {"path": "pkg/sub.py", "kind": "import-statement", "original": "pkg.sub"},
      {"path": "raylib", "kind": "import-statement", "external": true},
      {"path": "fast_codec", "kind": "import-statement", "missing": true}]},
    "pkg/__init__.py": {"bytes": 30, "imports": []},
    "pkg/sub.py": {"bytes": 51, "imports": []}
  },
  "outputs": {
    "app.c": {"bytes": 6011, "entryPoint": "app.py",
              "inputs": {"app.py": {"bytesInOutput": 412}, "pkg/__init__.py": {"bytesInOutput": 30},
                         "pkg/sub.py": {"bytesInOutput": 51}}}
  }
}
```

The import kinds are `import-statement`, `from-statement`, `lazy-import`,
`dynamic-import` (a literal `__import__`), and `include` (`-D`). A namespace
package has no file, so it is not an input. `--analyze` prints the same sizes
as a table on stderr, largest first.

### 7.2 Dependency file

`--deps FILE` writes a rule in the format C compilers write with `-MD`:

```make
app.c: app.py pkg/__init__.py pkg/sub.py
```

A Makefile that includes it rebuilds the C file when any bundled module
changes:

```make
app.c: app.py
	spyc --deps app.d -o $@ $<
-include app.d
```

### 7.3 Diagnostics

Messages go to stderr in the form C compilers use, with Python's own wording:

```text
app.py:3: error: No module named 'nosuch'
pkg/sub.py:1: error: attempted relative import beyond top-level package
pkg/bad.py:7: error: invalid syntax
app.py:12: warning: __import__ of a computed name cannot be bundled; name its modules with -D
spyc: error: -D plugins.nosuch: No module named 'plugins.nosuch'
```

Errors stop the build after the module that raised them has been walked, so
one run reports every missing import of that module. Under `-Werror`,
warnings count as errors.

## 8 esbuild feature map

Each esbuild option ([API reference](https://esbuild.github.io/api/)) is
listed with what spyc does with it. **Ported** keeps esbuild's meaning.
**Adapted** keeps its purpose in a Python form. **Not ported** gives the
reason.

| esbuild | spyc | Status |
| --- | --- | --- |
| bundle | always on: spyc follows imports. A program with no imports gives today's output plus an empty table. | Ported |
| entry points | `entry.py` or `-m MODULE`; several entries with `-c` | Ported |
| stdin, sourcefile | Not ported. Every module needs a path for `__file__` and its search root. | Not ported |
| loader (js, ts, json, text, file, binary, ...) | `.py` only. Embedded data files would need an in-memory `spy_mount`, a core change kept for later. | Not ported |
| platform | `-M` registers the standard modules a program may import without bundling them, as `--platform=node` treats Node's built-in modules. | Adapted |
| format (iife, cjs, esm) | standalone program, or `-c` for a host | Adapted |
| global name | `-N NAME`, as `qjsc -N` | Adapted |
| splitting | several `-c` entries share one module table | Adapted |
| outfile | `-o FILE` | Ported |
| outdir, outbase, entry/chunk/asset names, out extension, public path | Not ported. The output is one C file. | Not ported |
| allow overwrite | Refused: `-o` may not be an input. | Ported |
| write | Not ported. Use a temporary `-o`. | Not ported |
| banner, footer, charset, line limit | Not ported. The output is C, and these concern JavaScript text. | Not ported |
| legal comments | kept by `--minify` | Adapted |
| alias | `--alias NAME=TARGET` | Ported |
| external, packages=external | `-x MODULE` covers the module and its submodules | Ported |
| node paths, working directory | `-I DIR` roots; paths in output are relative to the working directory | Ported |
| main fields, conditions, resolve extensions, tsconfig, preserve symlinks | Not ported. Python has `.py` files and packages, and no manifests. | Not ported |
| target, supported, JSX options | Not ported. There is one language, PLS-315, and no lowering. Syntax errors fail the build. | Not ported |
| minify (whitespace) | `--minify`, keeping line numbers | Adapted |
| minify (identifiers), mangle props, keep names | Not ported. Names are observable through keyword arguments, `__dict__`, `getattr`, `locals()`, frames, and `__all__`, so renaming changes behavior. | Not ported |
| minify (syntax) | Not ported. Rewriting expressions would change evaluation order and the special methods called. | Not ported |
| tree shaking, pure, ignore annotations | Modules nothing imports are not bundled. Removing statements inside a module is not ported: top-level code may have side effects, and module attributes are reached dynamically. | Adapted |
| define | `-O` sets `__debug__`, the language's one build-time constant. `--alias` swaps configuration modules. Replacing other names would break `global` and attribute access. | Adapted |
| drop (debugger, console), drop labels | `-O` drops `assert`, `-OO` docstrings | Adapted |
| inject | Not ported. Import the module from the entry. | Not ported |
| sourcemap, source root, sources content | Not needed. Transforms keep line numbers ([6](#6-source-transforms)) and file names are the modules' own. | Adapted |
| metafile | `--metafile FILE` | Ported |
| analyze | `--analyze` | Ported |
| log level, log limit, log override, color, abs paths | errors and warnings on stderr, `-Werror` | Adapted |
| watch, serve, live reload, rebuild, cancel | `--deps FILE` for `make` | Adapted |
| plugins (onResolve, onLoad, onStart, onEnd) | Not ported. Resolution choices are `-I`, `-x`, `-D`, and `--alias`. Generated sources come from a build step that runs before spyc. | Not ported |
| dynamic `import()` with a template literal | `-D PKG.*` | Adapted |
| `require()` inside `try` | guarded imports ([3.4](#34-guarded-imports)) | Ported |

## 9 Implementation

### 9.1 Parsing with the engine

spyc includes `spy.c`, as `spy-worker.c` does. The build then sees the
engine's parser, source decoding (PEP 263, BOMs, newline normalization),
identifier normalization, and syntax errors, and spyc keeps no grammar of its
own. The walk over parsed units looks for `N_IMPORT` and `N_FROM` nodes, for
calls of the name `__import__`, and for the `try` statements that guard them.
`spyc` grows to the engine's size, which `qjsc` does as well.

The resolver ([3.1](#31-search-roots)) uses only C11 file operations:
`fopen` to read a file, and one portable directory listing so that names are
compared by exact spelling. The listing is the only POSIX call in spyc, and
spyc keeps it apart from the engine.

### 9.2 Plan

1. Resolver, discovery, the module table, the loader, `-I`, `-x`, `-D`, `-m`,
   and the diagnostics. The existing `tests/executable.py` checks keep
   passing. `examples/pong` adds `-x raylib` and installs `spy_pong_load`.
2. `--metafile`, `--deps`, and `--analyze`.
3. `-O`, `-OO`, and `--minify`, each checked by tokenizing again.
4. `--alias`, several `-c` entries, `-N`, and `-Werror`.
5. The manual's [2.3.2](manual.md#232-spyc-program-generator) and
   [4.2](manual.md#42-executable-generation) describe what is implemented,
   and this document loses its status note.

Each step turns more of `make test-build` green. Then `make test` runs it.

## 10 Verification

### 10.1 TLA+ model

`tests/tla/SpyBuild.tla` models resolution and discovery over a fixed tree of
two roots. The tree has a regular package, a subpackage, relative imports, a
namespace package split across both roots, a package shadowed by an earlier
root's module, a submodule that sits in the wrong root, a guarded missing
import, an external whose own import is missing, a module reachable only
through `-D`, and an import cycle. For every choice of externals and `-D`
names, and every order in which spyc may visit modules, TLC checks that:

- the build finishes, and fails exactly when an unguarded import, a relative
  import, or a `-D` name does not resolve;
- the bundle is the declarative closure of [3.2](#32-discovery), whatever the
  visiting order;
- every bundled module's parent is bundled, and nothing under an external
  prefix is;
- for every module name, the bundled loader either answers exactly as
  CPython's path finder does or does not answer at all. It never gives a
  different file, kind, or package. It does not answer only for names the
  build never reached (a computed import) and for externals, which it leaves
  to the host.

The import system over a loader is already modeled by `Imports.tla` and
replayed on spy. Together with this model, a bundled program imports what the
unbundled program imports.

### 10.2 Build tests

`tests/build` holds test262-style programs, one per behavior. Each program
checks itself with `assert` (or `raise SystemExit` under `-O`) and carries a
header:

```python
# build: -I lib -x ext
# bundles: main.py pkg/__init__.py pkg/sub.py lib/ns/b.py
# description: what the test shows
```

The test file is the entry (for `-m MODULE`, it is placed at that module's
path). Its sibling `NAME.fixtures/` holds the other modules. `# negative:
TEXT` marks a build that must fail with an error containing `TEXT`.
`tests/build_runner.py` runs each test in these phases:

1. **Oracle.** With `--oracle`, the pinned CPython runs the test unbundled,
   with the roots on `PYTHONPATH` and with `-O`, `-OO`, or `-m` as the build
   options say. The test must pass. A negative test must fail, and the
   oracle's output must contain spyc's message. This checks the test against
   Python itself. `# oracle: passes` marks a build that is stricter than the
   program's run: an import guarded only by its caller (`guard_scope.py`),
   or a `-D` name the program never imports. `# oracle: skip` exempts
   options that have no CPython equivalent (`--alias`).
2. **Build.** spyc builds the test twice, from two copies of the tree at
   different paths, and the two outputs must be identical. The metafile's
   inputs must be exactly the `# bundles:` list, and the `--deps` rule must
   name the same files.
3. **Run.** The C file is compiled against `libspy.a` (and `libspy-std.a` for
   `-M`). For `-c`, a generated host installs the loader and runs each entry.
   The program runs in an empty directory, so no source file is available.
   It must pass.

`make test-build` runs the suite against `./spyc`, and
`make test-build-oracle` adds the oracle phase. Until the bundler exists, the
build phase fails and the runner reports that for each test.
`tests/build_runner.py ./spyc --oracle-only PYTHON` runs the oracle phase
alone, which validates the tests before the bundler exists. All of them pass
on the pinned CPython 3.15.
