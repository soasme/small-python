"""
This module provides access to some objects used or maintained by the
interpreter and to functions that interact strongly with the interpreter.

Small Python's standard layer (spy-std.c) provides this module as
docs/std.md specifies it, after CPython 3.15's sys module. Runtime state
(modules, the handled exception, recursion and integer conversion limits,
host output, and the engine settings behind the lazy-import, asynchronous
generator, coroutine origin, and unraisable hooks) is native; the remaining
names are constant metadata describing this engine. _getframe() returns the
running frames; excepthook and unraisablehook write CPython's traceback
display without source lines. Tracing, profiling, monitoring, and audit hooks
are not provided.
"""

from _spy import (exception, getrecursionlimit, setrecursionlimit, get_int_max_str_digits,
                  set_int_max_str_digits, modules, maxsize, byteorder, platform, _getframe, lazy_modules,
                  getrefcount, getallocatedblocks,
                  _write, _flush, _frame_module, _tracked, _setting)


def _c_function(arity):
    # CPython's checks for a C function taking no argument or exactly one.
    def wrap(function):
        name = f"sys.{function.__name__}"

        def call(*args, **kwargs):
            if kwargs:
                raise TypeError(f"{name}() takes no keyword arguments")
            if len(args) != arity:
                raise TypeError(f"{name}() takes no arguments ({len(args)} given)" if not arity else
                                f"{name}() takes exactly one argument ({len(args)} given)")
            return function(*args)
        call.__name__, call.__doc__ = function.__name__, function.__doc__
        return call
    return wrap


def _structseq(name, fields, doc, instantiable=False, values=None, hidden=(), module="sys"):
    # A tuple type with named fields, as CPython's PyStructSequence; hidden
    # fields are reachable only by name.
    title = name if module == "builtins" else f"{module}.{name}"

    def __new__(cls, sequence, dict=None):
        sequence = tuple(sequence)
        if len(sequence) != len(fields):
            raise TypeError(f"{title}() takes a {len(fields)}-sequence ({len(sequence)}-sequence given)")
        return tuple.__new__(cls, sequence)

    def __repr__(self):
        return f"{title}(" + ", ".join(f"{field}={value!r}" for field, value in zip(fields, self)) + ")"

    def __reduce__(self):
        return type(self), (tuple(self),)

    namespace = {"__slots__": (), "__module__": module, "__doc__": doc, "__repr__": __repr__,
                 "__reduce__": __reduce__, "__match_args__": fields, "n_fields": len(fields) + len(hidden),
                 "n_sequence_fields": len(fields), "n_unnamed_fields": 0}
    if instantiable:
        namespace["__new__"] = __new__
    for index, field in enumerate(fields):
        namespace[field] = property(lambda self, index=index: tuple.__getitem__(self, index))
    for field, value in hidden:
        namespace[field] = property(lambda self, value=value: value)
    cls = type(name, (tuple,), namespace)
    if not instantiable:
        def __new__(cls, *args, **kwargs):
            raise TypeError(f"cannot create '{title}' instances")
        cls.__new__ = __new__
    return cls if values is None else tuple.__new__(cls, values)


version_info = _structseq("version_info", ("major", "minor", "micro", "releaselevel", "serial"),
                          "sys.version_info\n\nVersion information as a named tuple.",
                          values=(3, 15, 0, "final", 0))
hexversion = 0x030F00F0
version = "3.15.0 (Small Python)"
api_version = 1013
float_repr_style = "short"
maxunicode = 0x10FFFF

float_info = _structseq("float_info", ("max", "max_exp", "max_10_exp", "min", "min_exp", "min_10_exp",
                                       "dig", "mant_dig", "epsilon", "radix", "rounds"),
                        "sys.float_info\n\nA named tuple holding information about the float type.", True,
                        (1.7976931348623157e+308, 1024, 308, 2.2250738585072014e-308, -1021, -307,
                         15, 53, 2.220446049250313e-16, 2, 1))
# Integers are stored in 32-bit limbs; strings hash with 64-bit FNV-1a.
int_info = _structseq("int_info", ("bits_per_digit", "sizeof_digit", "default_max_str_digits",
                                   "str_digits_check_threshold"),
                      "sys.int_info\n\nA named tuple that holds information about Python's\n"
                      "internal representation of integers.", True, (32, 4, 4300, 640))
hash_info = _structseq("hash_info", ("width", "modulus", "inf", "nan", "imag", "algorithm",
                                     "hash_bits", "seed_bits", "cutoff"),
                       "hash_info\n\nA named tuple providing parameters used for computing\n"
                       "hashes. The attributes are read only.", True,
                       (64, (1 << 61) - 1, 314159, 0, 1000003, "fnv", 64, 0, 0))
flags = _structseq("flags", ("debug", "inspect", "interactive", "optimize", "dont_write_bytecode",
                             "no_user_site", "no_site", "ignore_environment", "verbose", "bytes_warning",
                             "quiet", "hash_randomization", "isolated", "dev_mode", "utf8_mode",
                             "warn_default_encoding", "safe_path", "int_max_str_digits"),
                   "sys.flags\n\nFlags provided through command line arguments or environment vars.",
                   values=(0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, False, 1, 0, True, 4300),
                   hidden=(("gil", 1), ("thread_inherit_context", 0), ("context_aware_warnings", 0),
                           ("lazy_imports", -1)))
# A context runs on its host's thread and has no lock of its own.
thread_info = _structseq("thread_info", ("name", "lock", "version"),
                         "sys.thread_info\n\nA named tuple holding information about the thread implementation.",
                         True, (None, None, None))


class _Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return "namespace(" + ", ".join(f"{key}={value!r}" for key, value in self.__dict__.items()) + ")"


implementation = _Namespace(name="smallpython", cache_tag=None, version=version_info, hexversion=hexversion)
abi_info = _Namespace(pointer_bits=64 if maxsize > 2**32 else 32, free_threaded=False, debug=False,
                      byteorder=byteorder)
abiflags = ""
builtin_module_names = ("_spy", "builtins", "gc", "sys")
stdlib_module_names = frozenset((
    "__future__", "_abc", "_aix_support", "_android_support", "_apple_support", "_ast", "_ast_unparse",
    "_asyncio", "_bisect", "_blake2", "_bz2", "_codecs", "_codecs_cn", "_codecs_hk", "_codecs_iso2022",
    "_codecs_jp", "_codecs_kr", "_codecs_tw", "_collections", "_collections_abc", "_colorize",
    "_compat_pickle", "_contextvars", "_csv", "_ctypes", "_curses", "_curses_panel", "_datetime",
    "_dbm", "_decimal", "_elementtree", "_frozen_importlib", "_frozen_importlib_external",
    "_functools", "_gdbm", "_hashlib", "_heapq", "_hmac", "_imp", "_interpchannels", "_interpqueues",
    "_interpreters", "_io", "_ios_support", "_json", "_locale", "_lsprof", "_lzma", "_markupbase",
    "_math_integer", "_md5", "_multibytecodec", "_multiprocessing", "_opcode", "_opcode_metadata",
    "_operator", "_osx_support", "_overlapped", "_pickle", "_posixshmem", "_posixsubprocess",
    "_py_abc", "_py_warnings", "_pydatetime", "_pydecimal", "_pyio", "_pylong", "_pyrepl", "_queue",
    "_random", "_remote_debugging", "_scproxy", "_sha1", "_sha2", "_sha3", "_signal", "_sitebuiltins",
    "_socket", "_sqlite3", "_sre", "_ssl", "_stat", "_statistics", "_string", "_strptime", "_struct",
    "_suggestions", "_symtable", "_sysconfig", "_thread", "_threading_local", "_tkinter", "_tokenize",
    "_tracemalloc", "_types", "_typing", "_uuid", "_warnings", "_weakref", "_weakrefset", "_winapi",
    "_wmi", "_zoneinfo", "_zstd", "abc", "annotationlib", "antigravity", "argparse", "array", "ast",
    "asyncio", "atexit", "base64", "bdb", "binascii", "bisect", "builtins", "bz2", "cProfile",
    "calendar", "cmath", "cmd", "code", "codecs", "codeop", "collections", "colorsys", "compileall",
    "compression", "concurrent", "configparser", "contextlib", "contextvars", "copy", "copyreg", "csv",
    "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal", "difflib", "dis", "doctest",
    "email", "encodings", "ensurepip", "enum", "errno", "faulthandler", "fcntl", "filecmp",
    "fileinput", "fnmatch", "fractions", "ftplib", "functools", "gc", "genericpath", "getopt",
    "getpass", "gettext", "glob", "graphlib", "grp", "gzip", "hashlib", "heapq", "hmac", "html",
    "http", "idlelib", "imaplib", "importlib", "inspect", "io", "ipaddress", "itertools", "json",
    "keyword", "linecache", "locale", "logging", "lzma", "mailbox", "marshal", "math", "mimetypes",
    "mmap", "modulefinder", "msvcrt", "multiprocessing", "netrc", "nt", "ntpath", "nturl2path",
    "numbers", "opcode", "operator", "optparse", "os", "pathlib", "pdb", "pickle", "pickletools",
    "pkgutil", "platform", "plistlib", "poplib", "posix", "posixpath", "pprint", "profile",
    "profiling", "pstats", "pty", "pwd", "py_compile", "pyclbr", "pydoc", "pydoc_data", "pyexpat",
    "queue", "quopri", "random", "re", "readline", "reprlib", "resource", "rlcompleter", "runpy",
    "sched", "secrets", "select", "selectors", "shelve", "shlex", "shutil", "signal", "site",
    "smtplib", "socket", "socketserver", "sqlite3", "ssl", "stat", "statistics", "string",
    "stringprep", "struct", "subprocess", "symtable", "sys", "sysconfig", "syslog", "tabnanny",
    "tarfile", "tempfile", "termios", "textwrap", "this", "threading", "time", "timeit", "tkinter",
    "token", "tokenize", "tomllib", "trace", "traceback", "tracemalloc", "tty", "turtle", "turtledemo",
    "types", "typing", "unicodedata", "unittest", "urllib", "uuid", "venv", "warnings", "wave",
    "weakref", "webbrowser", "winreg", "winsound", "wsgiref", "xml", "xmlrpc", "zipapp", "zipfile",
    "zipimport", "zlib", "zoneinfo"))
argv = []
orig_argv = []
path = []
meta_path = []
path_hooks = []
path_importer_cache = {}
warnoptions = []
_xoptions = {}
dont_write_bytecode = True
pycache_prefix = None
executable = ""
prefix = exec_prefix = base_prefix = base_exec_prefix = ""
platlibdir = "lib"
copyright = "Copyright (c) 2001 Python Software Foundation.\nAll Rights Reserved."


def _frames(frame_module):
    def _getframemodulename(depth=0):
        """Return the name of the module for a calling frame.

        The default depth returns the module containing the call to this API.
        A more typical use in a library will pass a depth of 1 to get the user's
        module rather than the library module.

        If no frame, module, or name can be found, returns None.
        """
        return frame_module(depth)
    return _getframemodulename


_getframemodulename = _frames(_frame_module)


@_c_function(0)
def exc_info():
    """Return current exception information: (type, value, traceback)."""
    exc = exception()
    return (None, None, None) if exc is None else (type(exc), exc, exc.__traceback__)


def exit(*args, **kwargs):
    """Exit the interpreter by raising SystemExit(status)."""
    if kwargs:
        raise TypeError("sys.exit() takes no keyword arguments")
    if len(args) > 1:
        raise TypeError(f"exit expected at most 1 argument, got {len(args)}")
    if not args or args[0] is None:
        raise SystemExit
    raise SystemExit(args[0])


def _interning():
    interned = {}

    @_c_function(1)
    def intern(string):
        """``Intern'' the given string."""
        if not isinstance(string, str):
            raise TypeError(f"intern() argument must be str, not {type(string).__name__}")
        if type(string) is not str:
            raise TypeError(f"can't intern {type(string).__name__}")
        return interned.setdefault(string, string)

    def getunicodeinternedsize(*args, _only_immortal=False):
        """Return the number of elements of the unicode interned dictionary"""
        if args:
            raise TypeError("getunicodeinternedsize() takes no positional arguments")
        return len(interned)
    return intern, getunicodeinternedsize


intern, getunicodeinternedsize = _interning()


@_c_function(0)
def getdefaultencoding():
    """Return the current default encoding used by the Unicode implementation."""
    return "utf-8"


@_c_function(0)
def getfilesystemencoding():
    """Return the encoding used to convert Unicode filenames to OS filenames."""
    return "utf-8"


@_c_function(0)
def getfilesystemencodeerrors():
    """Return the error mode used Unicode to OS filename conversion."""
    return "surrogateescape"


def call_tracing(*args, **kwargs):
    """Call func(*args), while tracing is enabled.

The tracing state is saved, and restored afterwards.  This is intended
to be called from a debugger from a checkpoint, to recursively debug
some other code."""
    if kwargs:
        raise TypeError("sys.call_tracing() takes no keyword arguments")
    if len(args) != 2:
        raise TypeError(f"call_tracing expected 2 arguments, got {len(args)}")
    if not isinstance(args[1], tuple):
        raise TypeError(f"call_tracing() argument 2 must be tuple, not {type(args[1]).__name__}")
    return args[0](*args[1])


@_c_function(0)
def is_remote_debug_enabled():
    """Return True if remote debugging is enabled, False otherwise."""
    return False


def _one_argument(name, keyword, args, kwargs):
    # A required argument given by position or keyword, as CPython's clinic parses it.
    if len(args) + len(kwargs) > 1:
        raise TypeError(f"{name}() takes at most 1 argument ({len(args) + len(kwargs)} given)")
    for key in kwargs:
        if key != keyword:
            raise TypeError(f"{name}() got an unexpected keyword argument '{key}'")
    if not args and not kwargs:
        raise TypeError(f"{name}() missing required argument '{keyword}' (pos 1)")
    return args[0] if args else kwargs[keyword]


def _settings(setting, structseq, one_argument, c_function):
    # Functions over the engine settings (_spy._setting).
    @c_function(0)
    def get_lazy_imports():
        """Gets the global lazy imports mode.

Returns "all" if all top level imports are potentially lazy.
Returns "normal" if only explicitly marked imports are potentially lazy."""
        return "normal" if setting("lazy_imports") is None else "all"

    def set_lazy_imports(*args, **kwargs):
        """Sets the global lazy imports mode.

The mode parameter must be one of the following strings:
- "all": All top-level imports become potentially lazy
- "normal": Only explicitly marked imports (with 'lazy' keyword) are lazy

In addition to the mode, lazy imports can be controlled via the filter
provided to sys.set_lazy_imports_filter"""
        mode = one_argument("set_lazy_imports", "mode", args, kwargs)
        if not isinstance(mode, str):
            raise TypeError("mode must be a string: 'normal' or 'all'")
        if mode not in ("normal", "all"):
            raise ValueError("mode must be 'normal' or 'all'")
        setting("lazy_imports", True if mode == "all" else None)

    @c_function(0)
    def get_lazy_imports_filter():
        """Get the current lazy imports filter function.

Returns the filter function if set, None otherwise."""
        return setting("lazy_imports_filter")

    def set_lazy_imports_filter(*args, **kwargs):
        """Set the lazy imports filter callback.

The filter is a callable which disables lazy imports when they
would otherwise be enabled. Returns True if the import is still enabled
or False to disable it. The callable is called with:

(importing_module_name, resolved_imported_module_name, [fromlist])

The first argument is the name of the module performing the import, the
second argument is the fully resolved name of the module being imported,
and the third argument is the list of names being imported (for 'from'
imports) or None (for regular 'import' statements)."""
        function = one_argument("set_lazy_imports_filter", "filter", args, kwargs)
        if function is not None and not callable(function):
            raise ValueError("filter provided but is not callable")
        setting("lazy_imports_filter", function)

    asyncgen_hooks = structseq("asyncgen_hooks", ("firstiter", "finalizer"), None, True, module="builtins")

    @c_function(0)
    def get_asyncgen_hooks():
        """Return the installed asynchronous generators hooks.

This returns a namedtuple of the form (firstiter, finalizer)."""
        return asyncgen_hooks((setting("firstiter"), setting("finalizer")))

    def set_asyncgen_hooks(*args, **kwargs):
        """set_asyncgen_hooks([firstiter] [, finalizer])

Set a finalizer for async generators objects."""
        if len(args) + len(kwargs) > 2:
            raise TypeError(f"function takes at most 2 arguments ({len(args) + len(kwargs)} given)")
        hooks = dict(zip(("firstiter", "finalizer"), args))
        for key, value in kwargs.items():
            if key not in ("firstiter", "finalizer"):
                raise TypeError(f"this function got an unexpected keyword argument '{key}'")
            if key in hooks:
                raise TypeError(f"argument for function given by name ('{key}') and position ({len(hooks)})")
            hooks[key] = value
        for key in ("finalizer", "firstiter"):
            if key in hooks and hooks[key] is not None and not callable(hooks[key]):
                raise TypeError(f"callable {key} expected, got {type(hooks[key]).__name__}")
        for key, value in hooks.items():
            setting(key, value)

    @c_function(0)
    def get_coroutine_origin_tracking_depth():
        """Check status of origin tracking for coroutine objects in this thread."""
        return setting("coroutine_origin_tracking_depth") or 0

    def set_coroutine_origin_tracking_depth(*args, **kwargs):
        """Enable or disable origin tracking for coroutine objects in this thread.

Coroutine objects will track 'depth' frames of traceback information
about where they came from, available in their cr_origin attribute.

Set a depth of 0 to disable."""
        depth = one_argument("set_coroutine_origin_tracking_depth", "depth", args, kwargs)
        if not isinstance(depth, int) and not hasattr(type(depth), "__index__"):
            raise TypeError(f"'{type(depth).__name__}' object cannot be interpreted as an integer")
        depth = range(depth).stop
        if not -2**31 <= depth < 2**31:
            raise OverflowError("Python int too large to convert to C int")
        if depth < 0:
            raise ValueError("depth must be >= 0")
        setting("coroutine_origin_tracking_depth", depth or None)
    return (get_lazy_imports, set_lazy_imports, get_lazy_imports_filter, set_lazy_imports_filter, get_asyncgen_hooks,
            set_asyncgen_hooks, get_coroutine_origin_tracking_depth, set_coroutine_origin_tracking_depth)


(get_lazy_imports, set_lazy_imports, get_lazy_imports_filter, set_lazy_imports_filter, get_asyncgen_hooks,
 set_asyncgen_hooks, get_coroutine_origin_tracking_depth,
 set_coroutine_origin_tracking_depth) = _settings(_setting, _structseq, _one_argument, _c_function)


@_c_function(0)
def is_finalizing():
    """Return True if Python is exiting."""
    return False


def _switching():
    microseconds = [5000]

    @_c_function(0)
    def getswitchinterval():
        """Return the current thread switch interval; see sys.setswitchinterval()."""
        return microseconds[0] / 1e6

    @_c_function(1)
    def setswitchinterval(interval):
        """Set the ideal thread switching delay inside the Python interpreter."""
        if not isinstance(interval, (int, float)) and not hasattr(type(interval), "__float__"):
            raise TypeError(f"must be real number, not {type(interval).__name__}")
        interval = float(interval)
        if interval <= 0.0:
            raise ValueError("switch interval must be strictly positive")
        microseconds[0] = int(interval * 1e6) if interval * 1e6 < 2**64 else 0
    return getswitchinterval, setswitchinterval


getswitchinterval, setswitchinterval = _switching()


def _sizes(tracked):
    def getsizeof(*args, **kwargs):
        """getsizeof(object [, default]) -> int

Return the size of object in bytes."""
        if len(args) + len(kwargs) > 2:
            raise TypeError(f"getsizeof() takes at most 2 arguments ({len(args) + len(kwargs)} given)")
        if not args and "object" not in kwargs:
            raise TypeError("getsizeof() missing required argument 'object' (pos 1)")
        for name in kwargs:
            if name not in ("object", "default"):
                raise TypeError(f"getsizeof() got an unexpected keyword argument '{name}'")
        if args and "object" in kwargs:
            raise TypeError("argument for getsizeof() given by name ('object') and position (1)")
        obj = args[0] if args else kwargs["object"]
        default = args[1:] or ((kwargs["default"],) if "default" in kwargs else ())
        method = getattr(type(obj), "__sizeof__", None)
        try:
            if method is None:
                raise TypeError(f"Type {type(obj).__name__} doesn't define __sizeof__")
            size = method(obj)
            if not isinstance(size, int):
                raise TypeError("an integer is required")
        except TypeError:
            if default:
                return default[0]
            raise
        if size > maxsize:
            raise OverflowError("Python int too large to convert to C ssize_t")
        if size < 0:
            raise ValueError("__sizeof__() should return >= 0")
        # Collected objects carry the collector's header, as in CPython.
        return size + 16 if tracked(obj) else size
    return getsizeof


getsizeof = _sizes(_tracked)


def _host_stream(write, flush):
    # Text written here goes to the host's output callback.
    class _HostStream:
        encoding = "utf-8"
        errors = "strict"

        def __init__(self, name):
            self.name = name

        def __repr__(self):
            return f"<sys stream name={self.name!r}>"

        def write(self, text, /):
            if not isinstance(text, str):
                raise TypeError(f"write() argument must be str, not {type(text).__name__}")
            write(text, self.name == "<stderr>")
            return len(text)

        def flush(self):
            flush()

        def writable(self):
            return True

        def readable(self):
            return False

        def isatty(self):
            return False
    return _HostStream("<stdout>"), _HostStream("<stderr>")


stdout, stderr = _host_stream(_write, _flush)
__stdout__, __stderr__ = stdout, stderr
stdin = __stdin__ = None


@_c_function(1)
def displayhook(value):
    """Print an object to sys.stdout and also save it in builtins._"""
    if value is None:
        return
    import builtins
    builtins._ = None
    stdout.write(repr(value) + "\n")
    builtins._ = value


def _traceback_display(value):
    # The traceback display of an exception, as CPython's traceback module
    # writes it; the host keeps no source lines to show beneath each frame.
    def safe(obj, what, function=str):
        try:
            return function(obj)
        except BaseException:
            return f"<{what} {function.__name__}() failed>"

    def stack(tb):
        lines, last, count = [], None, 0
        while tb is not None:
            code = tb.tb_frame.f_code
            entry = (code.co_filename, tb.tb_lineno, code.co_name)
            if entry != last:
                lines += repeated(count)
                last, count = entry, 0
            count += 1
            if count <= 3:
                lines.append(f'  File "{entry[0]}", line {entry[1]}, in {entry[2]}\n')
            tb = tb.tb_next
        return lines + repeated(count)

    def repeated(count):
        count -= 3
        return [f'  [Previous line repeated {count} more time{"s" if count > 1 else ""}]\n'] if count > 0 else []

    def type_name(cls):
        name, module = cls.__qualname__, cls.__module__
        if module in ("__main__", "builtins"):
            return name
        return f"{module if isinstance(module, str) else '<unknown>'}.{name}"

    def syntax_error(exc, name):
        lineno = None if exc.lineno is None else str(exc.lineno)
        end_lineno = None if exc.end_lineno is None else str(exc.end_lineno)
        suffix = ""
        if lineno is not None:
            yield f'  File "{exc.filename or "<string>"}", line {lineno}\n'
        elif exc.filename is not None:
            suffix = f" ({exc.filename})"
        text = exc.text
        if isinstance(text, str):
            rtext = text.rstrip("\n")
            ltext = rtext.lstrip(" \n\f")
            spaces = len(rtext) - len(ltext)
            offset = exc.offset
            if offset is None:
                yield f"    {ltext}\n"
            elif isinstance(offset, int):
                if lineno == end_lineno:
                    end = exc.end_offset if isinstance(exc.end_offset, int) and exc.end_offset != 0 else offset
                else:
                    end = len(rtext) + 1
                if text and offset > len(text):
                    offset = len(rtext) + 1
                if text and end > len(text):
                    end = len(rtext) + 1
                if offset >= end or end < 0:
                    end = offset + 1
                column, end_column = offset - 1 - spaces, end - 1 - spaces
                yield f"    {ltext}\n"
                if column >= 0:
                    yield "    " + " " * column + "^" * (end_column - column) + "\n"
        yield f"{name}: {exc.msg or '<no detail available>'}{suffix}\n"

    def exception_only(exc):
        name = type_name(type(exc))
        if isinstance(exc, SyntaxError):
            yield from syntax_error(exc, name)
        else:
            text = safe(exc, "exception")
            yield f"{name}: {text}\n" if text else f"{name}\n"
        try:
            notes = getattr(exc, "__notes__", None)
        except Exception as error:
            notes = [f"Ignored error getting __notes__: {safe(error, '__notes__', repr)}"]
        if isinstance(notes, (str, bytes)) or notes is not None and not (
                hasattr(type(notes), "__getitem__") and hasattr(type(notes), "__len__")) or isinstance(notes, dict):
            notes = [safe(notes, "__notes__", repr)]
        for note in notes or ():
            for line in safe(note, "note").split("\n"):
                yield line + "\n"

    def chain(exc, seen):
        # (message, exception) pairs, outermost first: the message introduces
        # the exception that follows it in the display.
        pairs = []
        while exc is not None:
            seen.add(id(exc))
            message, following = None, None
            if exc.__cause__ is not None and id(exc.__cause__) not in seen:
                message, following = cause, exc.__cause__
            elif exc.__context__ is not None and not exc.__suppress_context__ and id(exc.__context__) not in seen:
                message, following = context, exc.__context__
            pairs.append((message, exc))
            exc = following
        return pairs

    cause = "\nThe above exception was the direct cause of the following exception:\n\n"
    context = "\nDuring handling of the above exception, another exception occurred:\n\n"
    lines, state = [], {"depth": 0, "close": False}

    def emit(texts, margin="|"):
        prefix = "  " * state["depth"] + (margin + " " if state["depth"] else "")
        for text in [texts] if isinstance(texts, str) else texts:
            lines.extend(prefix + line for line in text.splitlines(True))

    def display(exc, seen):
        for message, exc in reversed(chain(exc, seen)):
            if message:
                emit(message)
            if not isinstance(exc, BaseExceptionGroup):
                if exc.__traceback__ is not None:
                    emit("Traceback (most recent call last):\n")
                    emit(stack(exc.__traceback__))
                emit(exception_only(exc))
            elif state["depth"] > 10:
                emit("... (max_group_depth is 10)\n")
            else:
                top = state["depth"] == 0
                state["depth"] += top
                if exc.__traceback__ is not None:
                    emit("Exception Group Traceback (most recent call last):\n", "+" if top else "|")
                    emit(stack(exc.__traceback__))
                emit(exception_only(exc))
                count = len(exc.exceptions)
                shown = count if count <= 15 else 16
                state["close"] = False
                for index in range(shown):
                    last = index == shown - 1
                    state["close"] = state["close"] or last
                    title = str(index + 1) if index < 15 else "..."
                    lines.append("  " * state["depth"] + ("+-" if index == 0 else "  ") +
                                 f"+---------------- {title} ----------------\n")
                    state["depth"] += 1
                    if index < 15:
                        display(exc.exceptions[index], seen)
                    else:
                        emit(f"and {count - 15} more exception{'s' if count - 15 > 1 else ''}\n")
                    if last and state["close"]:
                        lines.append("  " * state["depth"] + "+------------------------------------\n")
                        state["close"] = False
                    state["depth"] -= 1
                if top:
                    state["depth"] = 0

    display(value, set())
    return "".join(lines)


def _reporting(display):
    # The hooks that report exceptions, and the engine's way into the
    # unraisable one.
    UnraisableHookArgs = _structseq(
        "UnraisableHookArgs", ("exc_type", "exc_value", "exc_traceback", "err_msg", "object"),
        "UnraisableHookArgs\n\nType used to pass arguments to sys.unraisablehook.", True, module="builtins")

    def write(text):
        if stderr is not None:
            stderr.write(text)

    def show(value, traceback):
        # As CPython's PyErr_Display.
        if value is None:
            write("NoneType: None\n")
        elif not isinstance(value, BaseException):
            write(f"TypeError: print_exception(): Exception expected for value, {type(value).__name__} found\n")
        else:
            if traceback is not None and value.__traceback__ is None:
                value.__traceback__ = traceback
            write(display(value))

    def excepthook(*args, **kwargs):
        """Handle an exception by displaying it with a traceback on sys.stderr."""
        if kwargs:
            raise TypeError("excepthook() takes no keyword arguments")
        if len(args) != 3:
            raise TypeError(f"excepthook expected 3 arguments, got {len(args)}")
        show(args[1], args[2])

    @_c_function(1)
    def unraisablehook(unraisable):
        """Handle an unraisable exception.

The unraisable argument has the following attributes:

* exc_type: Exception type.
* exc_value: Exception value, can be None.
* exc_traceback: Exception traceback, can be None.
* err_msg: Error message, can be None.
* object: Object causing the exception, can be None."""
        if type(unraisable) is not UnraisableHookArgs:
            raise TypeError("sys.unraisablehook argument type must be UnraisableHookArgs")
        _, value, traceback, message, obj = unraisable
        if obj is not None:
            try:
                text = repr(obj)
            except BaseException:
                text = "<object repr() failed>"
            write(f"{message if message is not None else 'Exception ignored in'}: {text}\n")
        elif message is not None:
            write(f"{message}:\n")
        show(value, traceback)

    def report_unraisable(exc_type, value, traceback, message, obj):
        # The engine's unraisable hook (_spy._setting): calls sys.unraisablehook,
        # or the default when it is missing or fails.
        hook = globals().get("unraisablehook")
        try:
            (hook or unraisablehook)(UnraisableHookArgs((exc_type, value, traceback, message, obj)))
        except BaseException as error:
            unraisablehook(UnraisableHookArgs((type(error), error, error.__traceback__,
                                               "Exception ignored in sys.unraisablehook", hook)))
    return excepthook, unraisablehook, report_unraisable


excepthook, unraisablehook, _report_unraisable = _reporting(_traceback_display)
_setting("unraisablehook", _report_unraisable)


def breakpointhook(*args, **kwargs):
    """This hook function is called by built-in breakpoint().

Small Python has no debugger: the default hook does nothing."""


__displayhook__ = displayhook
__breakpointhook__ = breakpointhook
__excepthook__ = excepthook
__unraisablehook__ = unraisablehook

# Functions made inside the factories above are named as CPython's are.
for _function in (_getframemodulename, intern, getunicodeinternedsize, getswitchinterval, setswitchinterval,
                  getsizeof, exc_info, displayhook, getdefaultencoding, getfilesystemencoding,
                  getfilesystemencodeerrors, is_finalizing, is_remote_debug_enabled, get_lazy_imports,
                  get_lazy_imports_filter, get_asyncgen_hooks, get_coroutine_origin_tracking_depth, set_lazy_imports,
                  set_lazy_imports_filter, set_asyncgen_hooks, set_coroutine_origin_tracking_depth, call_tracing,
                  excepthook, unraisablehook):
    _function.__qualname__ = _function.__name__
del _function, _c_function, _one_argument, _settings, _traceback_display, _reporting, _report_unraisable, _structseq, _Namespace, _frames, _interning, _switching, _sizes, _host_stream
del _write, _flush, _frame_module, _tracked, _setting
