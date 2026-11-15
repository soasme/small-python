# spec: PLS-315 14.8, 6.2.1
# description: raise of an exception class whose Python __new__, which
# may loop, makes the exception: __new__ runs with the class, then, when
# it returns an instance of the class, its type's __init__; anything but
# an exception is a TypeError naming the class by its repr. A cause class
# is made after the exception, the same way, and another exception it
# returns, without __init__, is the cause. An exception from __new__ or __init__
# propagates instead, and a non-None __init__ result is a TypeError.
# Inside functions as at module level.
from harness import *

log = []

class Made(Exception):
    def __new__(cls, *a):
        for _ in (): pass
        log.append(("new", cls.__name__, a))
        return super().__new__(cls, *a)

class Both(Exception):
    def __new__(cls):
        for _ in (): pass
        log.append("new")
        return super().__new__(cls)
    def __init__(self):
        for _ in (): pass
        log.append("init")
        super().__init__("both")

class Child(Both):
    def __init__(self):
        for _ in (): pass
        log.append("child")

class Parent(Exception):
    def __new__(cls):
        for _ in (): pass
        return Exception.__new__(Child)

class Other(Exception):
    def __new__(cls):
        for _ in (): pass
        log.append("other")
        return KeyError("k")
    def __init__(self):
        log.append("never")

class Plain(Exception):
    def __new__(cls):
        for _ in (): pass
        return 3

class Raises(Exception):
    def __new__(cls):
        for _ in (): pass
        raise LookupError("new")

class BadInit(Exception):
    def __new__(cls):
        for _ in (): pass
        return super().__new__(cls)
    def __init__(self):
        for _ in (): pass
        return 1

def caught(f):
    try: f()
    except BaseException as e: return type(e).__name__, e.args, type(e.__cause__).__name__
    return None

def raises(cls, cause=0):
    def f():
        if cause == 0: raise cls
        raise cls from cause
    return f

def run():
    return [caught(raises(Made)), caught(raises(Both)), caught(raises(ValueError, Parent)), caught(raises(ValueError, Other)),
            caught(raises(Made, Both)), caught(raises(ValueError, Made)), caught(raises(Both, None)),
            caught(raises(Raises)), caught(raises(Made, Raises)), caught(raises(Raises, Made))]

expected = [("Made", (), "NoneType"), ("Both", ("both",), "NoneType"), ("ValueError", (), "Child"),
            ("ValueError", (), "KeyError"), ("Made", (), "Both"), ("ValueError", (), "Made"),
            ("Both", ("both",), "NoneType"), ("LookupError", ("new",), "NoneType"),
            ("LookupError", ("new",), "NoneType"), ("LookupError", ("new",), "NoneType")]
expected_log = [("new", "Made", ()), "new", "init", "other", ("new", "Made", ()), "new", "init",
                ("new", "Made", ()), "new", "init", ("new", "Made", ())]
assert_eq(run(), expected)
assert_eq(log, expected_log)
log.clear()

try: raise Made from Both
except Made as e: assert_eq((type(e.__cause__).__name__, e.__suppress_context__), ("Both", True))
assert_eq(log, [("new", "Made", ()), "new", "init"])

def errors():
    out = []
    for cls in (Plain, BadInit):
        try: raise cls
        except TypeError as e: out.append(str(e))
    try: raise ValueError from Plain
    except TypeError as e: out.append(str(e))
    return out

assert_eq(errors(), ["calling <class '__main__.Plain'> should have returned an instance of BaseException, not <class 'int'>",
                     "__init__() should return None, not 'int'",
                     "calling <class '__main__.Plain'> should have returned an instance of BaseException, not <class 'int'>"])
