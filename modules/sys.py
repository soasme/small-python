"""
This module provides access to some objects used or maintained by the
interpreter and to functions that interact strongly with the interpreter.

Small Python's standard layer (spy-std.c) provides this module as
docs/std.md specifies it, after CPython 3.15's sys module. Runtime state
(modules, the handled exception, recursion and integer conversion limits,
host output) is native; the remaining names are constant metadata
describing this engine. _getframe() returns the running frames. Tracing,
profiling, reference counts, audit hooks, and interpreter switching are not
provided.
"""

from _spy import (exception, getrecursionlimit, setrecursionlimit, get_int_max_str_digits,
                  set_int_max_str_digits, modules, maxsize, byteorder, platform, _getframe, lazy_modules,
                  getrefcount, getallocatedblocks,
                  _write, _flush, _frame_module, _tracked)


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


def _structseq(name, fields, doc, instantiable=False, values=None, hidden=()):
    # A tuple type with named fields, as CPython's PyStructSequence; hidden
    # fields are reachable only by name.
    def __new__(cls, sequence, dict=None):
        sequence = tuple(sequence)
        if len(sequence) != len(fields):
            raise TypeError(f"sys.{name}() takes a {len(fields)}-sequence ({len(sequence)}-sequence given)")
        return tuple.__new__(cls, sequence)

    def __repr__(self):
        return f"sys.{name}(" + ", ".join(f"{field}={value!r}" for field, value in zip(fields, self)) + ")"

    def __reduce__(self):
        return type(self), (tuple(self),)

    namespace = {"__slots__": (), "__module__": "sys", "__doc__": doc, "__repr__": __repr__,
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
            raise TypeError(f"cannot create 'sys.{name}' instances")
        cls.__new__ = __new__
    return tuple.__new__(cls, values)


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
            write(text)
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


def breakpointhook(*args, **kwargs):
    """This hook function is called by built-in breakpoint().

Small Python has no debugger: the default hook does nothing."""


__displayhook__ = displayhook
__breakpointhook__ = breakpointhook

# Functions made inside the factories above are named as CPython's are.
for _function in (_getframemodulename, intern, getunicodeinternedsize, getswitchinterval, setswitchinterval,
                  getsizeof, exc_info, displayhook, getdefaultencoding, getfilesystemencoding,
                  getfilesystemencodeerrors, is_finalizing):
    _function.__qualname__ = _function.__name__
del _function, _c_function, _structseq, _Namespace, _frames, _interning, _switching, _sizes, _host_stream
del _write, _flush, _frame_module, _tracked
