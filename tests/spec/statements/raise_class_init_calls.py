# spec: PLS-315 14.8
# description: raise of an exception class, and of a cause class after
# from, calls each class with no arguments, the exception's first, so a
# Python __init__ runs before the exception propagates; an __init__ that
# returns other than None raises TypeError, and an error from it
# propagates in place of the exception; in a function, a generator, a
# handler and a finally clause as at module level, with the traceback at
# the raise.
from harness import *

log = []

class E(Exception):
    def __init__(self, *args):
        log.append(("e", args))
        super().__init__(*args)

class C(Exception):
    def __init__(self):
        log.append("c")

class Returns(Exception):
    def __init__(self): return 1

class Fails(Exception):
    def __init__(self): raise KeyError("init")

def outcome(f):
    del log[:]
    try:
        f()
    except BaseException as e:
        return (type(e).__name__, e.args, type(e.__cause__).__name__, e.__suppress_context__,
                type(e.__context__).__name__, log[:])
    return "none"

def plain(): raise E
def caused(): raise E from C
def builtin_caused(): raise ValueError from C
def cause_first(): raise E("x") from E
def returns(): raise Returns
def fails(): raise Fails
def fails_cause(): raise E from Fails
def bad_cause(): raise E from 5
def handled():
    try: raise KeyError(1)
    except KeyError: raise E
def finishing():
    try: pass
    finally: raise E from None

cases = [plain, caused, builtin_caused, cause_first, returns, fails, fails_cause, bad_cause, handled, finishing]
expected = [
    ("E", (), "NoneType", False, "NoneType", [("e", ())]),
    ("E", (), "C", True, "NoneType", [("e", ()), "c"]),
    ("ValueError", (), "C", True, "NoneType", ["c"]),
    ("E", ("x",), "E", True, "NoneType", [("e", ("x",)), ("e", ())]),
    ("TypeError", ("__init__() should return None, not 'int'",), "NoneType", False, "NoneType", []),
    ("KeyError", ("init",), "NoneType", False, "NoneType", []),
    ("KeyError", ("init",), "NoneType", False, "NoneType", [("e", ())]),
    ("TypeError", ("exception causes must derive from BaseException",), "NoneType", False, "NoneType", [("e", ())]),
    ("E", (), "NoneType", False, "KeyError", [("e", ())]),
    ("E", (), "NoneType", True, "NoneType", [("e", ())]),
]
assert_eq([outcome(f) for f in cases], expected)

def gen():
    yield 1
    raise E from C

def in_generator():
    it = gen()
    next(it)
    next(it)

assert_eq(outcome(in_generator), ("E", (), "C", True, "NoneType", [("e", ()), "c"]))

def line():
    try:
        raise E
    except E as e:
        return e.__traceback__.tb_lineno - line.__code__.co_firstlineno
assert_eq(line(), 2)

del log[:]
try:
    raise E from C
except E as e:
    assert_eq((type(e.__cause__).__name__, log), ("C", [("e", ()), "c"]))
