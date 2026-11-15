# spec: PLS-315 14.8, 21.1.4
# description: raise of a class whose call returns an exception that is
# not an instance of the class raises the class called with that
# exception instead, after any cause is made and set on the first
# exception, not the second; a subclass's instance is raised as it is.
# When that second call raises, its exception propagates with the note
# "Normalization failed: type=NAME args=REPR", REPR <unknown> when the
# first exception's repr raises; when it returns no exception, a
# TypeError with that note. A class whose metaclass __call__ returns
# another exception normalizes the same way, and the cause of raise from
# such a class is the other exception. Inside functions as at module
# level, with __new__ in Python.
from harness import *

log = []

class Other(Exception):
    def __new__(cls, *a):
        for _ in (): pass
        log.append(("new", len(a)))
        if a: return super().__new__(cls, *a)
        return KeyError("k")
    def __init__(self, *a):
        for _ in (): pass
        log.append(("init", len(a)))

class Meta(type):
    def __call__(cls, *a):
        log.append(("call", len(a)))
        return KeyError("m") if not a else super().__call__(*a)

class ByMeta(Exception, metaclass=Meta): pass

class Strict(Exception):
    def __new__(cls):
        for _ in (): pass
        return KeyError("s")

class Odd(Exception):
    def __new__(cls, *a):
        for _ in (): pass
        return 5 if a else KeyError("o")

class BadRepr(Exception):
    def __repr__(self): raise ValueError

class Hidden(Exception):
    def __new__(cls):
        for _ in (): pass
        return BadRepr()

class Base(Exception): pass
class Kid(Base): pass

class Up(Base):
    def __new__(cls, *a):
        for _ in (): pass
        return Kid("up")

class Cause(Exception):
    def __init__(self):
        for _ in (): pass
        log.append("cause")

def show(e):
    first = e.args[0] if e.args and isinstance(e.args[0], BaseException) else None
    return (type(e).__name__, type(e.__cause__).__name__, e.__suppress_context__, getattr(e, "__notes__", None),
            type(first).__name__, type(first.__cause__).__name__ if first is not None else None)

def raised(cls, cause=None):
    try:
        if cause is None: raise cls
        raise cls from cause
    except BaseException as e: return show(e)

def run():
    return [raised(Other), raised(Other, Cause), raised(ByMeta), raised(ByMeta, ValueError), raised(Up),
            raised(ValueError, Other)]

expected = [("Other", "NoneType", False, None, "KeyError", "NoneType"),
            ("Other", "NoneType", False, None, "KeyError", "Cause"),
            ("ByMeta", "NoneType", False, None, "KeyError", "NoneType"),
            ("ByMeta", "NoneType", False, None, "KeyError", "ValueError"),
            ("Kid", "NoneType", False, None, "NoneType", None),
            ("ValueError", "KeyError", True, None, "NoneType", None)]
expected_log = [("new", 0), ("new", 1), ("init", 1), ("new", 0), "cause", ("new", 1), ("init", 1),
                ("call", 0), ("call", 1), ("call", 0), ("call", 1), ("new", 0)]
assert_eq(run(), expected)
assert_eq(log, expected_log)
log.clear()

assert_eq([raised(Other), raised(ByMeta, Cause)], [expected[0], ("ByMeta", "NoneType", False, None, "KeyError", "Cause")])
assert_eq(log, [("new", 0), ("new", 1), ("init", 1), ("call", 0), "cause", ("call", 1)])

def failures():
    out = []
    for cls in (Strict, Odd, Hidden):
        try: raise cls
        except TypeError as e: out.append((str(e), e.__notes__))
    try:
        try: raise LookupError
        except LookupError: raise Strict
    except TypeError as e: out.append(type(e.__context__).__name__)
    return out

assert_eq(failures(), [("Strict.__new__() takes 1 positional argument but 2 were given",
                        ["Normalization failed: type=Strict args=KeyError('s')"]),
                       ("calling <class '__main__.Odd'> should have returned an instance of BaseException, not int",
                        ["Normalization failed: type=Odd args=KeyError('o')"]),
                       ("Hidden.__new__() takes 1 positional argument but 2 were given",
                        ["Normalization failed: type=Hidden args=<unknown>"]),
                       "LookupError"])
