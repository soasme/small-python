# Replays OSErrors.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class MyOSError(OSError):
    pass


CLASSES = {"OSError": OSError, "FileNotFoundError": FileNotFoundError, "MyOSError": MyOSError}


def os_error(cls, errno, arity):
    args = [errno, "m", "f", None, "g"][:arity]
    e = CLASSES[cls](*args)
    return repr((type(e).__name__, e.errno, e.strerror, e.filename, e.filename2, str(e)))

SOURCES = {
    "six_args": "e = OSError(2, 'm', 'f', None, 'g', 'h')\nresult = (type(e).__name__, e.errno, e.args, str(e))",
    "none_errno": "e = OSError(None, 'm')\nresult = (type(e).__name__, e.errno, str(e))",
    "str_errno": "e = OSError('2', 'm')\nresult = (type(e).__name__, e.errno, str(e))",
    "args_kept": "e = OSError(2, 'm', 'f')\nresult = e.args",
    "blocking_written": "e = BlockingIOError(11, 'm', 3)\nresult = (e.characters_written, e.filename)",
    "blocking_unset": "BlockingIOError(11, 'm').characters_written",
    "blocking_delete": "e = BlockingIOError(11, 'm', 3)\ndel e.characters_written\nresult = hasattr(e, 'characters_written')",
    "attrs_writable": "e = OSError(1, 'm')\ne.errno = 7\ne.strerror = 's'\ne.filename = 'q'\nresult = (str(e), e.args)",
    "connection_family": 'result = [c.__name__ for c in (BrokenPipeError, ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError) if issubclass(c, ConnectionError)]',
    "timeout_alias": 'result = TimeoutError.__mro__[1].__name__',
    "kwargs_refused": 'result = OSError(errno=2)',
    "subclass_init_override": "class E(OSError):\n    def __init__(self, a):\n        super().__init__(a, 'x')\nresult = (type(E(2)).__name__, E(2).errno)",
    "subclass_new_override": "class E(OSError):\n    def __new__(cls, *a):\n        return super().__new__(cls, *a)\nresult = type(E(2, 'm')).__name__",
    "reduce": "e = OSError(2, 'm', 'f')\nresult = (e.__reduce__()[0].__name__, e.__reduce__()[1])",
    "filename_repr": "result = str(OSError(1, 'm', b'bytes\\xff'))",
    "filename_int": "result = str(OSError(1, 'm', 3))",
    "empty": 'e = OSError()\nresult = (e.errno, str(e), e.args)'
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}


def generated(p):
    return os_error(p["cls"], p["errno"], p["arity"])


def run(p):
    if "case" not in p:
        return generated(p)
    namespace = dict(TYPES)
    try:
        exec(compile(SOURCES[p["case"]], "<case>", "exec"), namespace)
        return repr(namespace.get("result"))
    except SyntaxError as error:
        return "%s: %s" % (type(error).__name__, error.msg)
    except Exception as error:
        return "%s: %s" % (type(error).__name__, error)


def outcome(p):
    # TLA+ strings are ASCII.
    return run(p).encode("ascii", "backslashreplace").decode()


check_programs(outcome)
