# Running CPython's Lib on Small Python

This document scopes one route to the Python 3.15 standard library: copy
CPython's `Lib/` tree unchanged and have Small Python supply what that tree
expects from the interpreter underneath it. It is a scope, not a status
report. Nothing listed here is implemented unless the [manual](manual.md)
says so, and per the project's rules no library module is added without an
explicit request.

## 1 The idea

CPython's standard library has two halves:

- `Lib/` holds about 600 Python modules (160 public top-level modules and
  packages, excluding `test`, `idlelib` and `turtledemo`). These are plain
  Python 3.15 source. Small Python can run them as they are.
- `Modules/`, `Python/` and `Objects/` hold the native modules that `Lib/`
  imports (`_io`, `_sre`, `_thread`, `posix`, `math`, ...). They are written
  against CPython's C API and internal headers, so they cannot be copied.
  Small Python must provide each one again, under the same name and with the
  same interface, written on its own C API.

So the plan is:

1. Copy `Lib/` byte for byte from the pinned tag (`v3.15.0`, the oracle under
   `tests/upstream/cpython`). Never patch a file in it. Updating to a later
   3.15 release means copying the tree again.
2. Provide the native modules that `Lib/` imports. They live at the host
   boundary, like `spy-std.c`, and stay out of `libspy.a`. The core keeps
   only `builtins`.
3. Close the engine and host gaps that `Lib/` reaches without importing a
   module: the import system, `sys`, code and frame objects (§3).

Small Python keeps its own `sys` and `gc` (`modules/`). In CPython these are
built in, not part of `Lib/`, so nothing gets copied over them.

## 2 How the lists were made

Every module under the pinned `Lib/` was parsed with the 3.15 oracle's `ast`.
An import counts as **required** when it runs at module level and is not
guarded by `except ImportError`. An import counts as **optional** when it is
guarded, sits inside a function, or sits under a platform test. Imports were
then followed through `Lib/` to the native modules they end at. Lazy imports
(`lazy import`) count as required, because the first use loads them.

The optional imports were then checked by hand. Many have a pure-Python
fallback (`_pydatetime`, `_pydecimal`, `_py_abc`, `_py_warnings`, Python code
in `heapq`, `bisect`, `json`, `pickle`, `operator`, `functools`). Others have
none, and in those cases a missing module means missing behaviour:

- `collections.deque` and `defaultdict` exist only in `_collections`.
- `hashlib` without `_md5`, `_sha1`, `_sha2`, `_sha3` or `_blake2` provides
  no hashes.
- `subprocess` on POSIX needs `_posixsubprocess`.

The tables below include those corrections. Windows-only modules (`nt`,
`_winapi`, `msvcrt`, `winreg`, `winsound`, `_overlapped`, `_wmi`) are listed
separately; the host targets POSIX first.

## 3 Prerequisites that are not modules

`Lib/` relies on the interpreter in ways that no native module covers.

**Import system.** `Lib/` needs these things from the importer:

- a `sys.path` search over a directory tree;
- packages with `__path__`, plus `__spec__`, `__loader__` and `__file__`;
- `sys.meta_path` and `sys.path_hooks`.

The `spy` command's loader currently resolves only paths next to the script
(manual §3.2). The route that fits "unchanged" best is the one CPython uses:
run `Lib/importlib/_bootstrap.py` and `_bootstrap_external.py` as the import
machinery, installed through `_imp`, and expose them as `_frozen_importlib`
and `_frozen_importlib_external`. `sys.implementation.cache_tag = None`
already turns off `.pyc` writing.

**`sys` surface.** The table below counts how often public `Lib/` modules
use names that Small Python's `sys` does not have yet. The names in place
include `path`, `meta_path`, `flags`, `_getframe`, `_getframemodulename` and
the hooks.

| name | uses in `Lib/` | used by |
|------|---------------:|---------|
| `sys.audit` | 55 | `os`, `socket`, `subprocess`, `urllib`, `shutil`, `tempfile`, ... |
| `sys.monitoring` | 22 | `bdb`, `pdb`, `profiling` |
| `sys._stdlib_dir` | 2 | `sysconfig`, `site` |

**Code, frame and traceback objects.** `inspect`, `traceback`, `dis`, `pdb`
and `doctest` read `co_positions()`, `co_lines()`, `co_code`, `f_lasti` and
`tb_lasti`. Small Python executes AST nodes, not CPython bytecode. Positions
and line tables can be real. `co_code`, `_opcode` and `dis` output describe
CPython's bytecode, so `dis` can import but cannot disassemble meaningfully.

**`compile` and `ast`.** `ast.parse` calls `compile(..., PyCF_ONLY_AST)`, and
`_ast` exposes the node classes. Both must expose the engine's own parse
tree, in CPython's node shapes.

**Language features.** `Lib/` 3.15 uses lazy imports, `frozendict` and
template strings throughout. All three are in the core already.

## 4 Native modules, in stages

### 4.1 Bootstrap set (19)

`traceback`, `os`, `re`, `io`, `threading`, `inspect`, `typing`, `warnings`
and `importlib` each pull in most of this set, so almost every real program
needs all of it:

| module | role |
|--------|------|
| `_io` | file, buffer, and text I/O classes behind `io` and `open` (`_pyio` imports `io`, so it is no fallback) |
| `posix` | `os` functions on POSIX; `os` is required by 94 public modules |
| `errno` | error-number constants |
| `time` | clocks, `struct_time`, `strftime` |
| `_thread` | locks, `RLock`, `start_new_thread`, `get_ident` |
| `_weakref` | `ref`, `proxy`, `getweakrefcount`; Small Python's weak table backs it |
| `_contextvars` | `ContextVar`, `Context`, `Token` |
| `_collections` | `deque`, `defaultdict`, `OrderedDict`, `_tuplegetter`, `_count_elements` |
| `itertools` | all iterator tools |
| `_operator` | `operator` accelerator; `hmac` imports `_compare_digest` from it directly |
| `_sre` | regular-expression engine under `re` |
| `_codecs` | codec registry, built-in codecs |
| `_warnings` | `warnings` filters (`_py_warnings` is a fallback) |
| `_imp` | import machinery hooks for `importlib._bootstrap` |
| `marshal` | serialization imported by `importlib._bootstrap_external` and `pkgutil` |
| `_ast` | AST node classes for `ast`, `inspect`, `dataclasses`, `annotationlib` |
| `_tokenize` | `TokenizerIter` for `tokenize`, `linecache`, `inspect` |
| `_typing` | `TypeVar`, `ParamSpec`, `Generic` support for `typing` |
| `_opcode` | bytecode metadata imported by `dis`, which `inspect` imports |

### 4.2 Portable services

These need only the C library. Each one makes the public modules in the last
column work.

| native | public modules it unlocks |
|--------|---------------------------|
| `math` | `datetime`, `decimal`, `fractions`, `random`, `statistics`, `tomllib`, `calendar`, ... (37) |
| `_struct` | `struct`, `pickle`, `zipfile`, `tarfile`, `gzip`, `wave`, `shelve` (28) |
| `binascii` | `base64`, `email`, `zipfile`, `ssl`, `secrets` (21) |
| `_random` | `random`, `tempfile`, `secrets`, `statistics`, `email` (17) |
| `_string` | `string`, `logging`, `email` (17) |
| `_signal` | `signal`, `subprocess`, `asyncio`, `unittest` (15) |
| `select` | `selectors`, `subprocess`, `asyncio`, `socketserver`, `pty` (12) |
| `atexit` | `logging`, `asyncio`, `unittest`, `multiprocessing` (9) |
| `_socket` | `socket`, `http`, `urllib`, `asyncio`, `smtplib`, `ftplib` (21) |
| `_posixsubprocess`, `fcntl` | `subprocess` |
| `pwd`, `grp` | `pathlib`, `shutil`, `tarfile`, `getpass` (optional) |
| `termios` | `tty`, `pty`, `getpass` |
| `_stat` | `stat` accelerator (fallback in `stat.py`) |
| `_md5`, `_sha1`, `_sha2`, `_sha3`, `_blake2`, `_hmac` | `hashlib`, `hmac`, and `random` seeding from `str`/`bytes`; CPython vendors portable HACL* C for these |
| `unicodedata` | `stringprep`, `encodings.idna`, `re` (optional), `traceback` (optional); built from Small Python's generated Unicode tables |
| `_csv` | `csv` |
| `_symtable` | `symtable` |
| `_locale` | `locale` (Python emulation otherwise) |
| `_multibytecodec`, `_codecs_cn`, `_codecs_hk`, `_codecs_iso2022`, `_codecs_jp`, `_codecs_kr`, `_codecs_tw` | CJK codecs in `encodings` |
| `array`, `mmap`, `cmath` | the modules of the same name |
| `_lsprof` | `cProfile` |
| `_tracemalloc`, `faulthandler` | the modules of the same name; need allocator and signal hooks in the engine |

### 4.3 Optional accelerators

`Lib/` already has a Python fallback for each of these, so skipping them is
correct, only slower:

| module | fallback |
|--------|----------|
| `_abc` | `_py_abc` |
| `_bisect`, `_heapq` | Python code in `bisect`, `heapq` |
| `_datetime` | `_pydatetime` |
| `_decimal` | `_pydecimal` |
| `_functools` | Python code in `functools` |
| `_json` | Python scanner in `json` |
| `_pickle` | Python code in `pickle` |
| `_elementtree` | Python code in `xml.etree.ElementTree` |
| `_statistics`, `_queue`, `_zoneinfo`, `_types`, `_uuid`, `_asyncio`, `_sysconfig`, `_suggestions` | Python code in the owning module |

### 4.4 External C libraries

CPython builds these against third-party libraries. Small Python allows no
runtime dependency beyond the C library and `libm` (AGENTS.md). Each module
below must either vendor its library as C source, as CPython does for expat
and libmpdec, or stay an opt-in build:

| module | library | public modules |
|--------|---------|----------------|
| `zlib` | zlib | `gzip`, `zipfile` (deflate), `compression` |
| `pyexpat` | expat (CPython vendors it) | `xml`, `plistlib`, `xmlrpc` |
| `_bz2` | libbz2 | `bz2` |
| `_lzma` | liblzma | `lzma` |
| `_zstd` | libzstd | `compression.zstd` |
| `_ssl`, `_hashlib` | OpenSSL | `ssl`; faster `hashlib` |
| `_sqlite3` | SQLite | `sqlite3`, `dbm.sqlite3` |
| `_ctypes` | libffi | `ctypes` |
| `_curses`, `_curses_panel` | ncurses | `curses` |
| `readline` | readline/libedit | interactive line editing (optional everywhere) |
| `_dbm`, `_gdbm` | ndbm, gdbm | `dbm.ndbm`, `dbm.gnu` |
| `_tkinter` | Tcl/Tk | `tkinter`, `turtle` |

### 4.5 Out of scope

- **Windows:** `nt`, `_winapi`, `msvcrt`, `winreg`, `winsound`,
  `_overlapped`, `_wmi`.
- **macOS proxy settings:** `_scproxy`. `urllib.request` treats it as
  optional.
- **CPython runtime internals:**
  - `_interpreters`, `_interpqueues` and `_interpchannels` (subinterpreters;
    `concurrent.interpreters`);
  - `_remote_debugging`;
  - `sys.monitoring` events at bytecode granularity.

  `concurrent.futures` imports `_interpreters` under `except ImportError`
  and simply omits `InterpreterPoolExecutor`, so this exclusion blocks only
  `concurrent.interpreters`. `_remote_debugging` is used only by
  `asyncio.tools` and `profiling.sampling`.
- **Process-based parallelism:** `_multiprocessing` and `_posixshmem`.
  `multiprocessing` spawns `sys.executable` and pickles across processes, so
  it needs a `spy` executable that can stand in for `python`.
- **CPython's own tests and examples:** `_testcapi`,
  `_testinternalcapi`, `_testbuffer`, `_testclinic*`, `_testmultiphase`,
  `_testsinglephase`, `_testimportmultiple`, `_xxtestfuzz`, `_ctypes_test`,
  `xxlimited*` and `xxsubtype`.

## 5 Per-module requirements

Sixteen public modules need no native module at all: `bisect` `cmd`
`colorsys` `copyreg` `enum` `graphlib` `heapq` `keyword` `linecache`
`mimetypes` `pydoc_data` `quopri` `stat` `this` `token` `types`. They still
need the prerequisites in §3.

Every other public module needs some or all of the bootstrap set (§4.1),
plus the natives listed for it below. An empty cell means the bootstrap set
is enough.

| public module | needs beyond the bootstrap set |
|---------------|--------------------------------|
| `abc` |  |
| `annotationlib` |  |
| `antigravity` | `_signal`, `_struct`, `binascii`, `math`, `pyexpat` |
| `argparse` |  |
| `ast` |  |
| `asyncio` | `_signal`, `_socket`, `_string`, `_struct`, `atexit`, `math`, `select` |
| `base64` | `binascii` |
| `bdb` |  |
| `bz2` | `_bz2` |
| `cProfile` | `_lsprof` |
| `calendar` | `math` |
| `code` |  |
| `codecs` |  |
| `codeop` |  |
| `collections` |  |
| `compileall` | `_struct` |
| `compression` | `_bz2`, `_lzma`, `_struct`, `_zstd`, `zlib` |
| `concurrent` | `_interpqueues`, `_interpreters`, `_signal`, `_socket`, `_string`, `_struct`, `atexit` |
| `configparser` |  |
| `contextlib` |  |
| `contextvars` |  |
| `copy` |  |
| `csv` | `_csv` |
| `ctypes` | `_ctypes`, `_signal`, `_struct` |
| `curses` | `_curses`, `_curses_panel` |
| `dataclasses` |  |
| `datetime` | `math` |
| `dbm` | `_dbm`, `_gdbm`, `_sqlite3`, `_struct`, `math` |
| `decimal` | `math` |
| `difflib` |  |
| `dis` |  |
| `doctest` | `_random`, `_sha2`, `_signal`, `_socket`, `_string`, `_struct`, `atexit`, `math`, `select` |
| `email` | `_random`, `_string`, `binascii`, `math` |
| `encodings` | `_bz2`, `_codecs_cn`, `_codecs_hk`, `_codecs_iso2022`, `_codecs_jp`, `_codecs_kr`, `_codecs_tw`, `_multibytecodec`, `binascii`, `unicodedata`, `zlib` |
| `ensurepip` | `_random`, `_sha2`, `_signal`, `math` |
| `filecmp` |  |
| `fileinput` |  |
| `fnmatch` |  |
| `fractions` | `math` |
| `ftplib` | `_socket` |
| `functools` |  |
| `genericpath` |  |
| `getopt` |  |
| `getpass` |  |
| `gettext` |  |
| `glob` |  |
| `gzip` | `_struct`, `zlib` |
| `hashlib` | `_blake2`, `_md5`, `_sha1`, `_sha2`, `_sha3` |
| `hmac` | `_blake2`, `_hmac`, `_md5`, `_sha1`, `_sha2`, `_sha3` |
| `html` |  |
| `http` | `_random`, `_socket`, `_string`, `binascii`, `math`, `select` |
| `imaplib` | `_random`, `_sha2`, `_signal`, `_socket`, `binascii`, `math` |
| `importlib` | `_random`, `_string`, `_struct`, `binascii`, `math` |
| `inspect` |  |
| `io` |  |
| `ipaddress` |  |
| `json` |  |
| `locale` |  |
| `logging` | `_socket`, `_string`, `_struct`, `atexit`, `math`, `select` |
| `lzma` | `_lzma` |
| `mailbox` | `_random`, `_sha2`, `_socket`, `_string`, `binascii`, `math` |
| `modulefinder` |  |
| `multiprocessing` | `_ctypes`, `_multiprocessing`, `_random`, `_signal`, `_socket`, `_struct`, `array`, `atexit`, `binascii`, `math`, `mmap`, `select` |
| `netrc` |  |
| `ntpath` |  |
| `nturl2path` |  |
| `numbers` |  |
| `opcode` |  |
| `operator` |  |
| `optparse` |  |
| `os` |  |
| `pathlib` |  |
| `pdb` | `_random`, `_sha2`, `_signal`, `_socket`, `_string`, `_struct`, `atexit`, `math`, `select` |
| `pickle` | `_struct` |
| `pickletools` | `_struct` |
| `pkgutil` |  |
| `platform` |  |
| `plistlib` | `_struct`, `binascii`, `math`, `pyexpat` |
| `poplib` | `_socket` |
| `posixpath` |  |
| `pprint` |  |
| `profile` |  |
| `profiling` | `_curses`, `_lsprof`, `_random`, `_remote_debugging`, `_signal`, `_socket`, `_struct`, `binascii`, `math`, `pyexpat`, `select` |
| `pstats` |  |
| `pty` | `select`, `termios` |
| `py_compile` |  |
| `pyclbr` |  |
| `pydoc` | `math` |
| `queue` |  |
| `random` | `_random`, `_sha2`, `math` |
| `re` |  |
| `reprlib` |  |
| `rlcompleter` | `atexit` |
| `runpy` |  |
| `sched` |  |
| `secrets` | `_random`, `_sha2`, `binascii`, `math` |
| `selectors` | `math`, `select` |
| `shelve` | `_struct` |
| `shlex` |  |
| `shutil` |  |
| `signal` | `_signal` |
| `site` |  |
| `smtplib` | `_random`, `_sha2`, `_socket`, `_string`, `binascii`, `math` |
| `socket` | `_socket` |
| `socketserver` | `_socket`, `math`, `select` |
| `sqlite3` | `_sqlite3`, `math` |
| `ssl` | `_socket`, `_ssl`, `binascii` |
| `statistics` | `_random`, `_sha2`, `math` |
| `string` | `_string` |
| `stringprep` | `unicodedata` |
| `struct` | `_struct` |
| `subprocess` | `_posixsubprocess`, `_signal`, `fcntl`, `select` |
| `symtable` | `_symtable` |
| `sysconfig` |  |
| `tabnanny` |  |
| `tarfile` | `_struct` |
| `tempfile` | `_random`, `_sha2`, `math` |
| `textwrap` |  |
| `threading` |  |
| `timeit` | `gc` |
| `tkinter` | `_tkinter` |
| `tokenize` |  |
| `tomllib` | `math` |
| `trace` | `_struct`, `gc` |
| `traceback` |  |
| `tracemalloc` | `_struct`, `_tracemalloc` |
| `tty` | `termios` |
| `turtle` | `_tkinter`, `math` |
| `typing` |  |
| `unittest` | `_signal`, `_socket`, `_string`, `_struct`, `atexit`, `math` |
| `urllib` | `_random`, `_socket`, `_string`, `binascii`, `math` |
| `uuid` |  |
| `venv` | `_signal`, `_string`, `atexit` |
| `warnings` |  |
| `wave` | `_struct` |
| `weakref` |  |
| `webbrowser` | `_signal`, `_struct`, `binascii`, `math`, `pyexpat` |
| `wsgiref` | `_socket`, `_string`, `binascii`, `math`, `select` |
| `xml` | `_random`, `_socket`, `_string`, `binascii`, `math`, `pyexpat` |
| `xmlrpc` | `_socket`, `_string`, `binascii`, `math`, `pyexpat`, `select` |
| `zipapp` | `_struct`, `binascii` |
| `zipfile` | `_struct`, `binascii` |
| `zipimport` | `_frozen_importlib`, `_frozen_importlib_external` |
| `zoneinfo` | `_struct`, `math` |
