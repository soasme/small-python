# PLS-STD-315: Small Python Standard Modules, Python 3.15

**Edition:** 2026, draft 1  
**Document identifier:** `PLS-STD-315:2026-draft1`  
**Library baseline:** CPython 3.15.0 (`v3.15.0`, commit `d220409a`), 64-bit Linux  
**Status:** Project library specification, draft

This document specifies the library modules of Small Python's standard layer
(`spy-std.c`): `sys` and `gc`. It follows CPython 3.15.0: a name this document
defines behaves as CPython's does, with CPython's signatures, results, and
error messages. Where CPython's behaviour depends on the process, the platform,
or the build, this document says so and lets the host choose.

The language itself is specified by [PLS-315](standards/3_15.md), which
depends on no library module. Its Annex B defines the host hooks that these
modules expose, and its Annex C.5 records how `sys` names correspond to
language facilities. This document specifies the modules themselves.

Each clause ends with a *Status* note on the current Small Python
implementation. Status notes are informative; they record gaps, not
permission to differ.

This is a project document of Small Python. It is not issued or endorsed by
the Python Software Foundation.

## Contents

1. [Scope](#1-scope)
2. [Conformance](#2-conformance)
3. [References](#3-references)
4. [Conventions](#4-conventions)
5. [The `sys` module](#5-the-sys-module)
6. [The `gc` module](#6-the-gc-module)
- [Annex A (informative) Implementation status](#annex-a-informative-implementation-status)
- [Annex B (informative) Verification](#annex-b-informative-verification)

## 1 Scope

This document specifies the public names of the modules `sys` and `gc` as
CPython 3.15.0 defines them, and their behaviour when called from Python code.
It does not specify:

- the language, including the objects these modules return that the language
  defines (frames, code objects, exceptions, tracebacks), which PLS-315 does;
- names beginning with an underscore, except `sys._getframe`,
  `sys._getframemodulename`, and `sys._xoptions`, which libraries rely on
  (5.15 lists the others);
- other library modules. Small Python provides no other library module; a
  host may add its own.

## 2 Conformance

A host that provides a module named here conforms to this document when each
name of that module that it binds behaves as specified. A host may leave a
name unbound; then reading it raises `AttributeError` as for any missing
module attribute. A host shall not bind a name to an object whose behaviour
differs from this document, except where a clause states a host choice.

A host conforms *fully* when it binds every name of a module. Small Python is
a partial implementation; Annex A lists its gaps.

The modules carry no other public names. Helpers used to build them shall be
private to the implementation, so that `dir(sys)` and `dir(gc)` list only the
names of this document and the CPython implementation details a host chooses
to add (5.15).

## 3 References

- PLS-315:2026-draft2, Python Language Specification, Python 3.15 Core
  Language (`docs/standards/3_15.md`).
- The Python Standard Library, version 3.15: *sys — System-specific parameters
  and functions*, and *gc — Garbage Collector interface*. Python Software
  Foundation.
- CPython 3.15.0 source: `Python/sysmodule.c`, `Modules/gcmodule.c`,
  `Python/clinic/sysmodule.c.h`, `Modules/clinic/gcmodule.c.h`, at commit
  `d220409a13b77de7a6c30abe16ea90db01528edc` (`tests/upstream.json`).

## 4 Conventions

Signatures use Python's notation: parameters before `/` are positional-only,
and a default shows the value an omitted argument takes.

"Raises a `ValueError` exception (*message*)" means the exception's single
argument is exactly *message*. Messages are CPython's, verbatim.

An argument "taken as an index" is converted as PLS-315 7.5.4 (ToIndexSize)
converts it: an object that is not an `int` and has no `__index__` raises a
`TypeError` exception ("'*T*' object cannot be interpreted as an integer"),
where *T* is its type's name.

*Host choice* marks behaviour the host decides, with CPython's choice given
as the recommended one.

A *structseq* is a tuple subclass with named fields, CPython's struct
sequence. Its type has the attributes `n_fields`, `n_sequence_fields`, and
`n_unnamed_fields`; each field is a read-only property; its `repr` is
*module*.*name*`(`*field*`=`*value*`, ...)`; it pickles as its type called
with a tuple of its values. Where a structseq is *constructible*, calling its
type with a sequence of exactly `n_sequence_fields` items returns a new
instance, and any other length raises a `TypeError` exception
("*module*.*name*() takes a *n*-sequence (*k*-sequence given)"). Otherwise
calling its type raises a `TypeError` exception ("cannot create
'*module*.*name*' instances").

## 5 The `sys` module

### 5.1 Modules and import

#### 5.1.1 `modules`

The module cache of PLS-315 17.3, as a `dict` mapping module names to module
objects.

*Status:* provided.

#### 5.1.2 `lazy_modules`

The pending names of lazy imports, %LazyModules% of PLS-315 17.5, as a
`set`.

*Status:* provided.

#### 5.1.3 `get_lazy_imports()`, `set_lazy_imports(mode)`

`get_lazy_imports()` returns the global lazy-imports mode, a `str`. `mode` is
`'normal'` (only `lazy import` statements are lazy) or `'all'` (every eligible
import is lazy). Any other value raises a `ValueError` exception ("mode must
be 'normal' or 'all'"). The initial mode is `'normal'`, unless the host sets
it from its command line or environment.

*Status:* not provided.

#### 5.1.4 `get_lazy_imports_filter()`, `set_lazy_imports_filter(filter)`

The filter is `None` or a callable that decides, for each potentially lazy
import, whether it is made lazy. `set_lazy_imports_filter(None)` removes it.
A filter that is not callable raises a `ValueError` exception ("filter
provided but is not callable"). `get_lazy_imports_filter()` returns the
current filter or `None`.

*Status:* not provided.

#### 5.1.5 `builtin_module_names`, `stdlib_module_names`

`builtin_module_names` is a `tuple` of the names of modules compiled into the
host, sorted. `stdlib_module_names` is a `frozenset` of the names of the
standard library's top-level modules, including those the host lacks.

*Host choice:* both list the host's modules; CPython's lists are those of a
CPython build. `builtin_module_names` includes `'sys'` and `'builtins'`.

*Status:* provided; `builtin_module_names` is `('_spy', 'builtins', 'gc',
'sys')`, and `stdlib_module_names` is CPython 3.15.0's.

#### 5.1.6 `path`, `meta_path`, `path_hooks`, `path_importer_cache`

The import system's search state: a `list` of path strings, a `list` of
meta-path finders, a `list` of path-entry hook callables, and a `dict` from
path entries to finders (or `None`). The import system consults them as
CPython's `importlib` does.

*Host choice:* a host whose module search is native (PLS-315 Annex B.1) may
bind them to empty containers it does not consult.

*Status:* bound to empty containers that the import system does not consult.

#### 5.1.7 `dont_write_bytecode`, `pycache_prefix`

`dont_write_bytecode` is a `bool`: when true, the import system writes no
bytecode cache files. `pycache_prefix` is `None` or the directory under which
they are written.

*Host choice:* a host that writes no bytecode binds `dont_write_bytecode` to
`True`.

*Status:* provided; `dont_write_bytecode` is `True` and `pycache_prefix` is
`None`.

### 5.2 The handled exception

#### 5.2.1 `exception()`

Returns the handled exception of PLS-315 9.5 (the exception being handled by
the innermost active `except` clause or `finally` cleanup), or `None`. Called
with any argument it raises a `TypeError` exception ("sys.exception() takes no
arguments (*n* given)").

*Status:* provided.

#### 5.2.2 `exc_info()`

Returns `(type(e), e, e.__traceback__)` for the handled exception *e*, or
`(None, None, None)`. Called with any argument it raises a `TypeError`
exception ("sys.exc_info() takes no arguments (*n* given)").

*Status:* provided.

### 5.3 Execution limits

#### 5.3.1 `getrecursionlimit()`, `setrecursionlimit(limit, /)`

The recursion limit of PLS-315 B.6. `getrecursionlimit()` returns it; its
initial value is 1000. `setrecursionlimit` takes *limit* as an index and:

1. If *limit* < 1, raises a `ValueError` exception ("recursion limit must be
   greater or equal than 1").
2. If *limit* does not fit a C `int`, raises an `OverflowError` exception
   ("Python int too large to convert to C int").
3. If *limit* is not greater than the current recursion depth *d*, raises a
   `RecursionError` exception ("cannot set the recursion limit to *limit* at
   the recursion depth *d*: the limit is too low").
4. Otherwise sets the limit and returns `None`.

*Status:* provided.

#### 5.3.2 `get_int_max_str_digits()`, `set_int_max_str_digits(maxdigits)`

The int string limit of PLS-315 22.1.8 and B.6; its initial value is 4300
unless the host sets it from its configuration, and 0 means unlimited.
`set_int_max_str_digits` takes *maxdigits*, by position or keyword, as an
index. A value other than 0 that is below 640 (`int_info.str_digits_check_threshold`)
raises a `ValueError` exception ("maxdigits must be >= 640 or 0 for
unlimited"). Called without it, it raises a `TypeError` exception
("set_int_max_str_digits() missing required argument 'maxdigits' (pos 1)").

*Status:* provided.

#### 5.3.3 `getswitchinterval()`, `setswitchinterval(interval, /)`

The thread switch interval in seconds, a `float`, initially 0.005.
`setswitchinterval` takes a real number; a value that is not positive raises
a `ValueError` exception ("switch interval must be strictly positive"), and a
value that is not a real number raises a `TypeError` exception ("must be real
number, not *T*").

*Host choice:* a host that runs one thread per context records the interval
and does not otherwise use it.

*Status:* provided; the interval is recorded only.

### 5.4 Frames

#### 5.4.1 `_getframe(depth=0, /)`

Returns the frame object (PLS-315 28.3) of the caller, or of its *depth*-th
caller. *depth* is taken as an index; a negative *depth* is treated as 0. If
the stack has fewer than *depth* + 1 frames, raises a `ValueError` exception
("call stack is not deep enough").

*Status:* provided. Frames carry `f_back`, `f_code`, `f_globals`, `f_locals`,
`f_lineno`, `f_lasti`, `f_builtins`, `f_trace`, and `f_generator`.

#### 5.4.2 `_getframemodulename(depth=0)`

Returns the `__name__` of the module of the caller's frame, or of its
*depth*-th caller, as `_getframe` would select it; returns `None` when there
is no such frame or module.

*Status:* provided.

### 5.5 Standard streams

#### 5.5.1 `stdin`, `stdout`, `stderr`

The objects of PLS-315 B.3: `print` writes to `stdout` by default, `input`
reads from `stdin`, and tracebacks and diagnostics go to `stderr`. Each
output stream has `write(s)`, which takes a `str` and returns the number of
characters written, `flush()`, and the attributes `encoding` and `errors`.
Assigning a new object to `sys.stdout` redirects `print`, display, and every
other use of the stream.

*Host choice:* CPython binds `io.TextIOWrapper` objects over the process's
file descriptors 0, 1, and 2, with encoding `'utf-8'` in UTF-8 mode and
errors `'surrogateescape'` for `stdin` and `stdout` and `'backslashreplace'`
for `stderr`. A host may bind any objects with those methods, or `None` for a
stream it lacks.

*Status:* `stdout` and `stderr` write to the host output callback, with
encoding `'utf-8'` and errors `'strict'`; `stdin` is `None` (`input` reads
through the host's input callback instead).

#### 5.5.2 `__stdin__`, `__stdout__`, `__stderr__`

The objects `stdin`, `stdout`, and `stderr` had when the context started, so
that a program can restore them.

*Status:* provided.

### 5.6 Hooks

A hook named `X` has a default bound both as `X` and as `__X__`; a program may
replace `X` and restore it from `__X__`.

#### 5.6.1 `displayhook(object, /)`

Implements HostDisplay (PLS-315 B.3.4). If *object* is `None`, does nothing.
Otherwise sets `builtins._` to `None`, writes `repr(object)` and `"\n"` to
`sys.stdout`, then sets `builtins._` to *object*. Called with a number of
arguments other than one, it raises a `TypeError` exception
("sys.displayhook() takes exactly one argument (*n* given)").

*Status:* provided.

#### 5.6.2 `excepthook(exctype, value, traceback, /)`

Implements HostReportException (PLS-315 B.4.2): writes the traceback display
of *value* (PLS-315 18.1.2, 18.1.3) to `sys.stderr`. The display uses
*traceback*, or *value*`.__traceback__` when *traceback* is `None`. Called
with a number of arguments other than three, it raises a `TypeError`
exception ("excepthook expected 3 arguments, got *n*").

*Status:* not provided; the host reports uncaught exceptions itself.

#### 5.6.3 `unraisablehook(unraisable, /)`

Implements HostReportUnraisable (PLS-315 B.4.3). *unraisable* is an
`UnraisableHookArgs` structseq with the fields `exc_type`, `exc_value`,
`exc_traceback`, `err_msg`, and `object`. The default writes *err_msg* (or
"Exception ignored in: " followed by the repr of *object*) and a line
terminator, then the traceback display of the exception, to `sys.stderr`. For
an exception raised by `__del__`, *err_msg* is "Exception ignored while
calling deallocator " followed by the repr of the `__del__` function.

*Status:* not provided; the engine reports ignored exceptions itself.

#### 5.6.4 `breakpointhook(*args, **kwargs)`

Implements HostBreakpoint (PLS-315 B.3.5); `breakpoint(*args, **kws)` calls
`sys.breakpointhook(*args, **kws)`. The default consults the environment
variable `PYTHONBREAKPOINT`: when it is `'0'` the hook returns `None`; when
it names a callable as *module*.*name*, the hook imports and calls it;
otherwise it calls `pdb.set_trace(*args, **kwargs)`.

*Host choice:* a host without a debugger or environment binds a default that
returns `None`.

*Status:* provided; the default returns `None`.

### 5.7 Exiting

#### 5.7.1 `exit(status=None, /)`

Raises `SystemExit`: when *status* is omitted or `None`, a `SystemExit` with
empty `args` (so its `code` is `None` and its `str` is `''`); otherwise
`SystemExit(status)`.
How the program then ends is PLS-315 B.4.4. Called with more than one
argument, it raises a `TypeError` exception ("exit expected at most 1
argument, got *n*").

*Status:* provided.

#### 5.7.2 `is_finalizing()`

Returns `True` while the interpreter is shutting down, and `False` otherwise.

*Status:* provided; always `False`, since a context never runs code while it
is freed.

### 5.8 Asynchronous generators and coroutines

#### 5.8.1 `get_asyncgen_hooks()`, `set_asyncgen_hooks(firstiter=..., finalizer=...)`

The hooks of PLS-315 B.5.1. `get_asyncgen_hooks()` returns an `asyncgen_hooks`
structseq with the fields `firstiter` and `finalizer`. `set_asyncgen_hooks`
takes either or both, by position or keyword; an omitted one is unchanged,
`None` removes it, and any other value that is not callable raises a
`TypeError` exception ("callable *name* expected, got *T*"). More than two
arguments raise a `TypeError` exception ("function takes at most 2 arguments
(*n* given)").

*Status:* not provided.

#### 5.8.2 `get_coroutine_origin_tracking_depth()`, `set_coroutine_origin_tracking_depth(depth)`

The number of frames recorded in a new coroutine's `cr_origin`, initially 0
(no tracking). A negative *depth* raises a `ValueError` exception ("depth
must be >= 0").

*Status:* not provided.

### 5.9 Interpreter description

These names describe the implementation. Unless a clause says otherwise, each
is set when the context starts and does not change.

#### 5.9.1 Version

- `version_info`: a structseq `sys.version_info`, not constructible, with the
  fields `major`, `minor`, `micro`, `releaselevel` (`'alpha'`, `'beta'`,
  `'candidate'`, or `'final'`), and `serial`; for this baseline
  `(3, 15, 0, 'final', 0)`. As a tuple it compares with tuples, so
  `sys.version_info >= (3, 15)` holds.
- `hexversion`: the same as one `int`, `0x030F00F0`.
- `version`: a `str` beginning with the version number, then build details.
- `api_version`: the C API version, 1013.
- `implementation`: a namespace object with at least `name` (the
  implementation's name in lower case), `cache_tag` (the tag of bytecode cache
  files, or `None` when they are not written), `version` (a value like
  `version_info` for the implementation), and `hexversion`.
- `copyright`: the copyright notice, a `str`.

*Host choice:* `version` after the number, `implementation`, and `copyright`.

*Status:* provided; `implementation.name` is `'smallpython'`, its `cache_tag`
is `None`, and its version is the language version.

#### 5.9.2 Numbers

- `maxsize`: the largest index-size value of PLS-315 Annex D, 2<sup>63</sup> − 1
  on 64-bit hosts.
- `maxunicode`: 1114111 (`0x10FFFF`).
- `float_info`: a constructible structseq `sys.float_info` with the fields
  `max`, `max_exp`, `max_10_exp`, `min`, `min_exp`, `min_10_exp`, `dig`,
  `mant_dig`, `epsilon`, `radix`, and `rounds`, describing IEEE 754 binary64:
  `(1.7976931348623157e+308, 1024, 308, 2.2250738585072014e-308, -1021, -307,
  15, 53, 2.220446049250313e-16, 2, 1)`.
- `float_repr_style`: `'short'`, since `repr` of a float gives the shortest
  string that converts back to it.
- `int_info`: a constructible structseq `sys.int_info` with the fields
  `bits_per_digit`, `sizeof_digit`, `default_max_str_digits` (4300), and
  `str_digits_check_threshold` (640). CPython's digits are 30 bits in 4
  bytes.
- `hash_info`: a constructible structseq `sys.hash_info` with the fields
  `width`, `modulus`, `inf`, `nan`, `imag` (the hash constants of PLS-315
  22.1.9: 64, 2<sup>61</sup> − 1, 314159, 0, 1000003), `algorithm`,
  `hash_bits`, `seed_bits`, and `cutoff`. CPython's `str` and `bytes` hash is
  `'siphash13'`, with 64 hash bits, 128 seed bits, and cutoff 0.

*Host choice:* the digit size of `int_info` and the string hash of
`hash_info` (`algorithm`, `hash_bits`, `seed_bits`, `cutoff`), as PLS-315
Annex D allows.

*Status:* provided. `int_info` reports 32-bit digits in 4 bytes, and
`hash_info` the algorithm `'fnv'` (64-bit FNV-1a, unseeded) with 64 hash
bits, 0 seed bits, and cutoff 0.

#### 5.9.3 Platform

- `byteorder`: `'little'` or `'big'`, the native byte order.
- `platform`: the platform identifier, such as `'linux'`, `'darwin'`, or
  `'win32'`.
- `abiflags`: the ABI flags of the build, `''` for a default build.
- `abi_info`: a namespace object with `pointer_bits` (64 on 64-bit hosts),
  `free_threaded`, `debug`, and `byteorder`.
- `thread_info`: a constructible structseq `sys.thread_info` with the fields
  `name` (the thread implementation, such as `'pthread'`), `lock`, and
  `version`.
- `platlibdir`: the name of the platform library directory, such as `'lib'`.

*Status:* provided, except `thread_info`: a context has no threads of its
own to describe.

#### 5.9.4 Installation and command line

- `executable`: the path of the interpreter binary, or `''` when unknown.
- `prefix`, `exec_prefix`, `base_prefix`, `base_exec_prefix`: installation
  directories, `str`.
- `argv`: the command-line arguments of the program, a `list` of `str` whose
  first item is the script name.
- `orig_argv`: the interpreter's own command line, a `list` of `str`.
- `warnoptions`: the `-W` options, a `list` of `str`.
- `_xoptions`: the `-X` options, a `dict`.
- `flags`: a structseq `sys.flags`, not constructible, of the command-line and
  environment settings. Its 18 sequence fields are `debug`, `inspect`,
  `interactive`, `optimize`, `dont_write_bytecode`, `no_user_site`,
  `no_site`, `ignore_environment`, `verbose`, `bytes_warning`, `quiet`,
  `hash_randomization`, `isolated`, `dev_mode` (a `bool`), `utf8_mode`,
  `warn_default_encoding`, `safe_path` (a `bool`), and `int_max_str_digits`;
  it also has four fields reachable only by name: `gil`,
  `thread_inherit_context`, `context_aware_warnings`, and `lazy_imports`, so
  `n_fields` is 22 and `n_sequence_fields` is 18. `flags.optimize` is the
  optimization level of PLS-315 B.6.

*Host choice:* every value, from the host's own command line and
environment; a host without them binds empty values and the flags of an
isolated interpreter.

*Status:* provided, with empty strings and lists; `flags` reports an
isolated interpreter that writes no bytecode.

### 5.10 Text

#### 5.10.1 `intern(string, /)`

Returns the canonical object for strings equal to *string*, entering
*string* as that object if none is recorded, so that equal interned strings
are the same object. A non-`str` raises a `TypeError` exception ("intern()
argument must be str, not *T*"); an instance of a `str` subclass raises a
`TypeError` exception ("can't intern *T*").

*Status:* provided.

#### 5.10.2 `getdefaultencoding()`, `getfilesystemencoding()`, `getfilesystemencodeerrors()`

Return `'utf-8'`, the encoding of file names (`'utf-8'` in UTF-8 mode), and
the error handler for file names (`'surrogateescape'` on POSIX hosts).

*Status:* provided, returning `'utf-8'`, `'utf-8'`, and `'surrogateescape'`.

### 5.11 Memory and object introspection

- `getrefcount(object, /)`: the reference count of *object*, an `int`
  (including the temporary reference of the argument). Called with a number
  of arguments other than one, it raises a `TypeError` exception
  ("sys.getrefcount() takes exactly one argument (*n* given)").
- `getsizeof(object, default=...)`: the size of *object* in bytes as its
  type's `__sizeof__` reports it, plus the collector's header (16 bytes) for
  tracked objects. If `__sizeof__` is missing, raises a `TypeError`, or
  returns a non-`int` (a `TypeError` exception, "an integer is required"),
  the result is *default* when given and the `TypeError` otherwise; other
  exceptions propagate. A result above `maxsize` raises an `OverflowError`
  exception ("Python int too large to convert to C ssize_t"), and a negative
  one a `ValueError` exception ("__sizeof__() should return >= 0"). Both
  parameters may be given by keyword; without *object* it raises a
  `TypeError` exception ("getsizeof() missing required argument 'object'
  (pos 1)"), and with more than two arguments a `TypeError` exception
  ("getsizeof() takes at most 2 arguments (*n* given)").
- `getallocatedblocks()`: the number of memory blocks the allocator has in
  use. Called with any argument it raises a `TypeError` exception
  ("sys.getallocatedblocks() takes no arguments (*n* given)").
- `getunicodeinternedsize()`: the number of interned strings. Called with a
  positional argument it raises a `TypeError` exception
  ("getunicodeinternedsize() takes no positional arguments").

*Host choice:* the sizes and counts, as PLS-315 Annex D allows for
`__sizeof__`.

*Status:* provided; `getallocatedblocks()` counts the context's live values.

### 5.12 Tracing, profiling, monitoring, and auditing

`settrace(function, /)`, `gettrace()`, `setprofile(function, /)`,
`getprofile()`, `call_tracing(func, args, /)`, the `monitoring` namespace
(PEP 669), `addaudithook(hook)`, `audit(event, /, *args)`,
`activate_stack_trampoline(backend, /)`, `deactivate_stack_trampoline()`,
`is_stack_trampoline_active()`, `remote_exec(pid, script)`, and
`is_remote_debug_enabled()` are CPython's debugger, profiler, audit, and
remote-debugging interfaces, specified by the CPython documentation for
version 3.15.

*Host choice:* whether to provide them. A host that provides one provides it
as CPython specifies.

*Status:* not provided.

### 5.13 Dynamic loading

`getdlopenflags()` and `setdlopenflags(flags, /)` read and set the flags
used to load extension modules with `dlopen`.

*Host choice:* a host that loads no extension modules leaves them unbound.

*Status:* not provided.

### 5.14 Threads

Every function of this clause that takes a thread argument and the names
`_current_frames` and `_current_exceptions` concern the threads of one
interpreter. A Small Python context runs on one thread at a time.

*Status:* not provided.

### 5.15 CPython implementation details

CPython also binds `_base_executable`, `_baserepl`, `_clear_internal_caches`,
`_clear_type_cache`, `_current_exceptions`, `_current_frames`,
`_debugmallocstats`, `_dump_tracelets`, `_framework`,
`_get_cpu_count_config`, `_git`, `_home`, `_is_gil_enabled`, `_is_immortal`,
`_is_interned`, `_jit`, `_setprofileallthreads`, `_settraceallthreads`, and
`_stdlib_dir`. They describe or control CPython's own build and runtime; this
document does not specify them, and a host need not bind them.

*Status:* none is bound.

## 6 The `gc` module

The `gc` module controls the cycle collector of PLS-315 9.7, which reclaims
groups of unreachable objects that refer to each other. Reference counting
reclaims other objects without it.

### 6.1 Collection

#### 6.1.1 `collect(generation=2)`

Runs a collection of the given generation and the younger ones, finalizes
and reclaims the unreachable objects found, and returns their number, an
`int`. *generation* is taken as an index, by position or keyword; a value
outside 0 to 2 raises a `ValueError` exception ("invalid generation"). Before
and after the collection, it calls each item of `gc.callbacks` (6.3.2).

*Host choice:* the number of generations a host's collector distinguishes;
a collector with one generation collects everything for any valid
*generation*.

*Status:* provided; the collector has one generation.

### 6.2 Automatic collection

The collector also runs automatically, when allocations outnumber
deallocations by the thresholds.

#### 6.2.1 `enable()`, `disable()`, `isenabled()`

`enable()` and `disable()` turn automatic collection on and off;
`isenabled()` returns whether it is on. It is on initially.

*Host choice:* when collections run automatically. A host that collects only
when it is asked to (PLS-315 9.7) records the setting.

*Status:* provided; the setting is recorded, and the engine collects when the
host asks.

#### 6.2.2 `get_threshold()`, `set_threshold(threshold0[, threshold1[, threshold2]])`

`get_threshold()` returns the three thresholds as a `tuple`, initially
`(2000, 10, 10)`. `set_threshold` sets the first one, two, or three of them,
each taken as an index that fits a C `long` (a larger one raises an
`OverflowError` exception, "Python int too large to convert to C long").
Setting *threshold0* to 0 disables automatic collection. Any other number of
arguments raises a `TypeError` exception ("gc.set_threshold requires 1 to 3
arguments").

*Status:* provided, recorded only.

#### 6.2.3 `get_count()`

Returns the current collection counts as a `tuple` of three `int`s.

*Status:* provided; always `(0, 0, 0)`.

### 6.3 Statistics and callbacks

#### 6.3.1 `get_stats()`

Returns a `list` of three `dict`s, one per generation, each with the keys
`'collections'` (the number of collections), `'collected'` (the objects
collected), `'uncollectable'` (the objects found uncollectable),
`'candidates'` (the objects considered), and `'duration'` (the total time
spent, in seconds, a `float`).

*Status:* provided; `'candidates'` counts the context's live values, and
`'duration'` is 0.0 where the C library lacks `timespec_get`.

#### 6.3.2 `callbacks`

A `list` of callables, initially empty, that `collect` and automatic
collections call as *callback*(*phase*, *info*): *phase* is `'start'` before
a collection and `'stop'` after it, and *info* is a `dict` with the keys
`'generation'`, `'collected'`, `'uncollectable'`, `'candidates'`, and
`'duration'` (a `float`, in seconds); the last four are 0 in the `'start'`
call.

*Status:* provided.

### 6.4 Object queries

#### 6.4.1 `get_objects(generation=None)`

Returns a `list` of the objects the collector tracks, excluding the list
returned. With *generation*, only those in that generation. *generation* is
`None` or an `int`: another type raises a `TypeError` exception ("argument
should be integer or None, not '*T*'"), and a value of 3 or more raises a
`ValueError` exception ("generation parameter must be less than the number
of available generations (3)"). A negative value returns the objects of all
generations.

*Status:* provided; the single generation holds every tracked object.

#### 6.4.2 `get_referents(*objs)`, `get_referrers(*objs)`

`get_referents` returns a `list` of the objects that the arguments refer to
directly and that the collector can find (an `int` refers to none).
`get_referrers` returns a `list` of the tracked objects that refer directly
to any argument.

*Status:* provided.

#### 6.4.3 `is_tracked(obj, /)`

Returns whether the collector tracks *obj*. Atomic values (`None`, numbers,
`str`, `bytes`) and containers that can hold only such values (including
tuples, and frozensets, of untracked items) are untracked; lists,
dictionaries, instances, functions, and classes that are not static types are
tracked. Called with a number of arguments other than one, it raises a
`TypeError` exception ("gc.is_tracked() takes exactly one argument (*n*
given)").

*Host choice:* which values are tracked, beyond what CPython's rule implies.

*Status:* provided.

#### 6.4.4 `is_finalized(obj, /)`

Returns whether the collector has run *obj*'s finalizer (PEP 442), which
happens at most once.

*Status:* provided.

### 6.5 Debugging and garbage

#### 6.5.1 `get_debug()`, `set_debug(flags, /)`, `DEBUG_*`

`set_debug` takes *flags* as an index and sets the debugging flags, initially
0; `get_debug()` returns them. The flags are `DEBUG_STATS` (1, print
statistics), `DEBUG_COLLECTABLE` (2, print collectable objects found),
`DEBUG_UNCOLLECTABLE` (4, print uncollectable objects found),
`DEBUG_SAVEALL` (32, append unreachable objects to `gc.garbage` instead of
freeing them), and `DEBUG_LEAK` (38, the last three together). Printed
information goes to `sys.stderr`.

*Status:* provided, except that `DEBUG_STATS`, `DEBUG_COLLECTABLE`, and
`DEBUG_UNCOLLECTABLE` print nothing.

#### 6.5.2 `garbage`

A `list` of objects the collector found unreachable but could not free, and,
under `DEBUG_SAVEALL`, of every unreachable object found.

*Status:* provided; no object is uncollectable, so it holds only what
`DEBUG_SAVEALL` saves.

### 6.6 Freezing

`freeze()` moves every tracked object to a permanent generation that
collections ignore; `unfreeze()` returns them to the oldest generation;
`get_freeze_count()` returns the number of objects in the permanent
generation. `freeze()` and `unfreeze()` return `None`.

*Status:* provided; nothing is frozen, and `get_freeze_count()` is 0.

## Annex A (informative) Implementation status

The status of Small Python's standard layer against this document, as of the
date of this edition. "Deviates" means the name is bound but differs as its
clause's status note states; a host choice the document allows is not a
deviation.

| Module | Bound as specified | Deviates | Not bound |
| --- | --- | --- | --- |
| `sys` | every name of clause 5 not listed in the other columns | none | `get_lazy_imports`, `set_lazy_imports`, `get_lazy_imports_filter`, `set_lazy_imports_filter` (5.1.3, 5.1.4); `excepthook`, `unraisablehook` (5.6.2, 5.6.3); `get_asyncgen_hooks`, `set_asyncgen_hooks`, `get_coroutine_origin_tracking_depth`, `set_coroutine_origin_tracking_depth` (5.8); `thread_info` (5.9.3); the interfaces of 5.12 to 5.14 |
| `gc` | every name of clause 6 not listed in the other columns | `get_count` (6.2.3); `set_debug` (6.5.1); `freeze`, `unfreeze`, `get_freeze_count` (6.6) | none |

The unbound names need the engine to call them or to keep new state: a
traceback display for `excepthook`, reports of ignored exceptions for
`unraisablehook`, the hooks of PLS-315 27.5.4, the global lazy-import mode,
coroutine origins, and line events for tracing.

## Annex B (informative) Verification

Every value and message quoted in clauses 5 and 6 was checked against the
pinned CPython 3.15.0 build (`make oracle`, `tests/upstream/cpython-build`),
on 64-bit Linux, by calling the name from Python and reading the result or
the exception. Values that depend on the build (`version`, paths,
`builtin_module_names`, `thread_info.version`) are described rather than
quoted.

`tests/std.py`, part of `make test`, keeps the two in step: it runs
`tests/std_probe.py`, which prints what this document states about each name
Small Python binds, under the `spy` command and under the Python 3.15 running
it, and fails unless the outputs are identical.
