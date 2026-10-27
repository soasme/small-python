# Replays ExceptionHierarchy.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
import builtins
NAMES = sorted(n for n in dir(builtins) if isinstance(getattr(builtins, n), type) and issubclass(getattr(builtins, n), BaseException) and not n.startswith("_"))


def hierarchy(name):
    cls = getattr(builtins, name)
    return repr(([c.__name__ for c in cls.__mro__], cls.__module__))

SOURCES = {
    "exception_misses_base": "try:\n    try:\n        raise SystemExit(3)\n    except Exception:\n        result = 'caught'\nexcept BaseException as e:\n    result = ('escaped', type(e).__name__, e.code)",
    "aliases": 'result = (EnvironmentError is OSError, IOError is OSError)',
    "warning_raisable": "try:\n    raise DeprecationWarning('old')\nexcept Warning as w:\n    result = (type(w).__name__, w.args)",
    "group_bases": 'result = (ExceptionGroup.__bases__, BaseExceptionGroup.__bases__)',
    "subclass_catch": "try:\n    {}['k']\nexcept LookupError as e:\n    result = type(e).__name__",
    "not_subclass_catch": "try:\n    try:\n        1 / 0\n    except LookupError:\n        result = 'wrong'\nexcept ArithmeticError as e:\n    result = type(e).__name__",
    "bool_base_flags": "result = [n for n in ('SystemExit', 'KeyboardInterrupt', 'GeneratorExit', 'BaseExceptionGroup') if not issubclass(eval(n), Exception)]",
    "multiple_inheritance_ok": 'class E(ValueError, KeyError): pass\nresult = [c.__name__ for c in E.__mro__]',
    "layout_conflict": 'class E(OSError, UnicodeError): pass',
    "raise_non_exception": 'raise 1',
    "raise_class_instantiates": 'try:\n    raise KeyError\nexcept KeyError as e:\n    result = (type(e).__name__, e.args)',
    "raise_class_bad_init": 'class E(Exception):\n    def __init__(self, x): pass\nraise E'
}




def generated(p):
    return hierarchy(p["name"])


def run(p):
    if "case" not in p:
        return generated(p)
    namespace = {}
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
