# spec: PLS-315 14.8, 21.1.4
# description: raise of a class whose Python __new__, which may loop,
# returns an exception of another class calls the class again with that
# exception: its __new__, then, for an instance of the class, its Python
# __init__ with the exception, each of which may loop. The second
# instance is raised; an exception from either call, an __init__ that
# returns other than None, or a __new__ that returns no exception raises
# its error with the "Normalization failed" note. The cause of raise
# from is set on the first exception. Inside functions as at module level.
from harness import *

log = []

class Other(Exception): pass

class Again(Exception):
    def __new__(cls, *a):
        for _ in (): pass
        log.append(("new", len(a)))
        return super().__new__(cls, *a) if a else Other("o")
    def __init__(self, *a):
        for _ in (): pass
        log.append(("init", type(a[0]).__name__ if a else None))
        if a and a[0].args == ("raise",): raise LookupError("init")
        if a and a[0].args == ("value",): return 1

def make(text):
    class Made(Again):
        def __new__(cls, *a):
            for _ in (): pass
            return super().__new__(cls, *a) if a else Other(text)
    return Made

class Bare(Exception):
    def __new__(cls, *a):
        for _ in (): pass
        if a: raise KeyError("new")
        return Other("b")

def caught(k, cause=None):
    try:
        if cause: raise k from cause
        raise k
    except BaseException as e:
        args = e.args if not isinstance(e, Again) else tuple(type(x).__name__ for x in e.args)
        first = e.args[0] if e.args and isinstance(e.args[0], BaseException) else None
        return (type(e).__name__, args, getattr(e, "__notes__", None),
                type(first.__cause__).__name__ if first else None, type(e.__cause__).__name__)

def run():
    return [caught(Again), caught(make("raise")), caught(make("value")), caught(Bare), caught(Again, KeyError)]

expected = [("Again", ("Other",), None, "NoneType", "NoneType"),
            ("LookupError", ("init",), ["Normalization failed: type=Made args=Other('raise')"], None, "NoneType"),
            ("TypeError", ("__init__() should return None, not 'int'",), ["Normalization failed: type=Made args=Other('value')"], None, "NoneType"),
            ("KeyError", ("new",), ["Normalization failed: type=Bare args=Other('b')"], None, "NoneType"),
            ("Again", ("Other",), None, "KeyError", "NoneType")]
expected_log = [("new", 0), ("new", 1), ("init", "Other"), ("new", 1), ("init", "Other"),
                ("new", 1), ("init", "Other"), ("new", 0), ("new", 1), ("init", "Other")]
assert_eq(run(), expected)
assert_eq(log, expected_log)
log.clear()

assert_eq([caught(Again), caught(make("raise"))], expected[:2])
assert_eq(log, expected_log[:5])
