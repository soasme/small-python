"""
This module provides access to some objects used or maintained by the
interpreter and to functions that interact strongly with the interpreter.

Small Python's standard layer (spy-std.c) provides this module, following CPython 3.15's sys
module. Runtime state (modules, the handled exception, recursion and integer
conversion limits, host output) is native; the remaining names are constant
metadata describing this engine. _getframe() returns the running frames.
Tracing, profiling, reference counts, audit hooks, and interpreter switching
are not provided.
"""

from _spy import (exception, getrecursionlimit, setrecursionlimit, get_int_max_str_digits,
                  set_int_max_str_digits, modules, maxsize, byteorder, platform, _write, _flush,
                  _getframe, _frame_module, lazy_modules)


def _structseq(name, fields, doc, instantiable=False):
    # A tuple type with named fields, as CPython's PyStructSequence.
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
                 "__reduce__": __reduce__, "__match_args__": fields, "n_fields": len(fields),
                 "n_sequence_fields": len(fields), "n_unnamed_fields": 0}
    if instantiable:
        namespace["__new__"] = __new__
    for index, field in enumerate(fields):
        namespace[field] = property(lambda self, index=index: tuple.__getitem__(self, index))
    cls = type(name, (tuple,), namespace)
    if not instantiable:
        def __new__(cls, *args, **kwargs):
            raise TypeError(f"cannot create 'sys.{name}' instances")
        cls.__new__ = __new__
    return cls


def _make(cls, values):
    return tuple.__new__(cls, values)


version_info = _make(_structseq("version_info", ("major", "minor", "micro", "releaselevel", "serial"),
                                "sys.version_info\n\nVersion information as a named tuple."),
                     (3, 15, 0, "final", 0))
hexversion = 0x030F00F0
version = "3.15.0 (Small Python)"
api_version = 1013
float_repr_style = "short"
maxunicode = 0x10FFFF

float_info = _make(_structseq("float_info", ("max", "max_exp", "max_10_exp", "min", "min_exp", "min_10_exp",
                                             "dig", "mant_dig", "epsilon", "radix", "rounds"),
                              "sys.float_info\n\nA named tuple holding information about the float type.", True),
                   (1.7976931348623157e+308, 1024, 308, 2.2250738585072014e-308, -1021, -307,
                    15, 53, 2.220446049250313e-16, 2, 1))
# Integers are stored in 32-bit limbs; strings hash with 64-bit FNV-1a.
int_info = _make(_structseq("int_info", ("bits_per_digit", "sizeof_digit", "default_max_str_digits",
                                         "str_digits_check_threshold"),
                            "sys.int_info\n\nA named tuple that holds information about Python's\n"
                            "internal representation of integers."),
                 (32, 4, 4300, 640))
hash_info = _make(_structseq("hash_info", ("width", "modulus", "inf", "nan", "imag", "algorithm",
                                           "hash_bits", "seed_bits", "cutoff"),
                             "hash_info\n\nA named tuple providing parameters used for computing\n"
                             "hashes. The attributes are read only."),
                  (64, (1 << 61) - 1, 314159, 0, 1000003, "fnv", 64, 0, 0))
flags = _make(_structseq("flags", ("debug", "inspect", "interactive", "optimize", "dont_write_bytecode",
                                   "no_user_site", "no_site", "ignore_environment", "verbose", "bytes_warning",
                                   "quiet", "hash_randomization", "isolated", "dev_mode", "utf8_mode",
                                   "warn_default_encoding", "safe_path", "int_max_str_digits"),
                         "sys.flags\n\nFlags provided through command line arguments or environment vars."),
              (0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, False, 1, 0, True, 4300))


class _Implementation:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return "namespace(" + ", ".join(f"{key}={value!r}" for key, value in self.__dict__.items()) + ")"


implementation = _Implementation(name="smallpython", cache_tag=None, version=version_info, hexversion=hexversion)
builtin_module_names = ("_thread", "_typing", "_weakref", "builtins", "collections", "gc", "itertools", "sys", "types", "weakref")
argv = []
orig_argv = []
path = []
meta_path = []
path_hooks = []
path_importer_cache = {}
warnoptions = []
_xoptions = {}
dont_write_bytecode = True
executable = ""
prefix = exec_prefix = base_prefix = base_exec_prefix = ""
copyright = "Copyright (c) 2001 Python Software Foundation.\nAll Rights Reserved."


def _getframemodulename(depth=0):
    """Return the name of the module for a calling frame.

    The default depth returns the module containing the call to this API.
    A more typical use in a library will pass a depth of 1 to get the user's
    module rather than the library module.

    If no frame, module, or name can be found, returns None.
    """
    return _frame_module(depth)


def exc_info():
    """Return current exception information: (type, value, traceback)."""
    exc = exception()
    return (None, None, None) if exc is None else (type(exc), exc, exc.__traceback__)


def exit(status=None, /):
    """Exit the interpreter by raising SystemExit(status)."""
    raise SystemExit(status)


_interned = {}


def intern(string, /):
    """``Intern'' the given string."""
    if not isinstance(string, str):
        raise TypeError(f"intern() argument must be str, not {type(string).__name__}")
    if type(string) is not str:
        raise TypeError(f"can't intern {type(string).__name__}")
    return _interned.setdefault(string, string)


def getdefaultencoding():
    """Return the current default encoding used by the Unicode implementation."""
    return "utf-8"


def getfilesystemencoding():
    """Return the encoding used to convert Unicode filenames to OS filenames."""
    return "utf-8"


def getfilesystemencodeerrors():
    """Return the error mode used Unicode to OS filename conversion."""
    return "surrogateescape"


def is_finalizing():
    """Return True if Python is exiting."""
    return False


class _HostStream:
    # Text written here goes to the host's output callback.
    encoding = "utf-8"
    errors = "strict"

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"<sys stream name={self.name!r}>"

    def write(self, text, /):
        if not isinstance(text, str):
            raise TypeError(f"write() argument must be str, not {type(text).__name__}")
        _write(text)
        return len(text)

    def flush(self):
        _flush()

    def writable(self):
        return True

    def readable(self):
        return False

    def isatty(self):
        return False


stdout = __stdout__ = _HostStream("<stdout>")
stderr = __stderr__ = _HostStream("<stderr>")
stdin = __stdin__ = None


def displayhook(value, /):
    """Print an object to sys.stdout and also save it in builtins._"""
    if value is None:
        return
    import builtins
    builtins._ = None
    stdout.write(repr(value) + "\n")
    builtins._ = value


__displayhook__ = displayhook
