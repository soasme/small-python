# spec: PLS-315 14.8, 21.1.4
# description: raise of an exception class, or from a cause class, whose
# metaclass has a Python __call__, which may loop, calls it with no
# arguments; its result is raised as made, with no __init__ after it, and
# one of another class calls the class raised again with it, after the
# cause is made, the cause then left behind. A result that is not an
# exception raises TypeError, and an error from the __call__ propagates.
# Inside functions as at module level.
from harness import *

log = []

class Other(Exception): pass

class M(type):
    def __call__(cls, *a):
        for _ in (): pass
        log.append(("call", cls.__name__, tuple(map(repr, a))))
        if cls.__name__ == "Swap" and not a: return Other("o")
        if cls.__name__ == "NotExc": return 5
        if cls.__name__ == "Boom": raise LookupError("boom")
        return super().__call__(*a)

class E(Exception, metaclass=M):
    def __init__(self, *a):
        log.append("init")
        super().__init__(*a)

class Swap(Exception, metaclass=M): pass
class NotExc(Exception, metaclass=M): pass
class Boom(Exception, metaclass=M): pass

class N(Exception):
    def __new__(cls, *a):
        for _ in (): pass
        log.append(("new", a))
        return super().__new__(cls, *a)

class S2(Exception):
    def __new__(cls, *a):
        for _ in (): pass
        log.append(("s2", tuple(map(repr, a))))
        return Other("x") if not a else super().__new__(cls, *a)

def outcome(f):
    try: f()
    except BaseException as e:
        c = e.__cause__
        args = tuple(repr(x) if isinstance(x, BaseException) else x for x in e.args)
        out = (type(e).__name__, args, type(c).__name__ if c else None, list(log))
        log.clear()
        return out

def r1(): raise E
def r2(): raise Swap
def r3(): raise NotExc
def r4(): raise Boom
def r5(): raise Other from E
def r6(): raise S2 from E
def r7(): raise Swap from N
def r8(): raise E from Boom
def r9(): raise S2 from NotExc
def r10(): raise E from E

def raises():
    return [outcome(r) for r in (r1, r2, r3, r4, r5, r6, r7, r8, r9, r10)]

made = "calling <class '" + NotExc.__module__ + ".NotExc'> should have returned an instance of BaseException, not <class 'int'>"
expected = [
    ("E", (), None, [("call", "E", ()), "init"]),
    ("Swap", ("Other('o')",), None, [("call", "Swap", ()), ("call", "Swap", ("Other('o')",))]),
    ("TypeError", (made,), None, [("call", "NotExc", ())]),
    ("LookupError", ("boom",), None, [("call", "Boom", ())]),
    ("Other", (), "E", [("call", "E", ()), "init"]),
    ("S2", ("Other('x')",), None, [("s2", ()), ("call", "E", ()), "init", ("s2", ("Other('x')",))]),
    ("Swap", ("Other('o')",), None, [("call", "Swap", ()), ("new", ()), ("call", "Swap", ("Other('o')",))]),
    ("LookupError", ("boom",), None, [("call", "E", ()), "init", ("call", "Boom", ())]),
    ("TypeError", (made,), None, [("s2", ()), ("call", "NotExc", ())]),
    ("E", (), "E", [("call", "E", ()), "init", ("call", "E", ()), "init"]),
]
assert_eq(raises(), expected)
assert_eq(log, [])

assert_eq([outcome(r1), outcome(r7)], [expected[0], expected[6]])
try: raise Swap from N
except Swap as e: assert_eq((repr(e.args[0]), e.__cause__), ("Other('o')", None))
assert_eq(log, expected[6][3])
