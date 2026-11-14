# spec: PLS-315 19.3.21, 19.3.22
# description: isinstance and issubclass of objects that are not classes read
# __bases__ and __class__ through their Python properties and __getattr__
# fallbacks in protocol order, a tuple target trying each item in turn,
# called directly or with starred arguments;
# searching several bases counts toward the recursion depth; inside
# functions as at module level.
from harness import *

log = []

class Bases:
    def __init__(self, bases, name): self.b, self.name = bases, name
    @property
    def __bases__(self):
        for _ in range(1): pass
        log.append(("bases", self.name))
        return self.b
    def __repr__(self): return self.name

A = Bases((), "A"); B = Bases((A,), "B"); C = Bases((B, A), "C"); D = Bases((C,), "D")

class Inst:
    def __init__(self, cls): self.cls = cls
    @property
    def __class__(self):
        for _ in range(1): pass
        log.append("class")
        return self.cls

class Getattr:
    def __getattr__(self, name):
        for _ in range(1): pass
        log.append(("getattr", name))
        return (A,) if name == "__bases__" else None

class NoBases: pass

def run(f, *args):
    for _ in range(1): pass
    log.clear()
    try: r = f(*args)
    except Exception as ex: r = (type(ex).__name__, str(ex))
    return r, log[:]

cases = [
    (issubclass, D, A),
    (issubclass, D, Bases((), "Z")),
    (isinstance, Inst(D), A),
    (isinstance, Inst(D), (Bases((), "Y"), A)),
    (isinstance, Inst(int), int),
    (isinstance, Inst(bool), int),
    (isinstance, 1, D),
    (issubclass, Getattr(), A),
    (issubclass, NoBases(), A),
    (issubclass, D, NoBases()),
    (isinstance, 1, NoBases()),
    (issubclass, int, D),
    (isinstance, Inst(D), (int, str, C)),
]

def bases(*names): return [("bases", n) for n in names]

arg2 = "a class, a tuple of classes, or a union"
expected = [
    (True, bases("D", "A", "D", "C", "B")),
    (False, bases("D", "Z", "D", "C", "B", "A", "A")),
    (True, bases("A") + ["class"] + bases("D", "C", "B")),
    (True, bases("Y") + ["class"] + bases("D", "C", "B", "A", "A", "A")
        + ["class"] + bases("D", "C", "B")),
    (True, ["class"]),
    (True, ["class"]),
    (False, bases("D")),
    (True, [("getattr", "__bases__")] + bases("A") + [("getattr", "__bases__")]),
    (("TypeError", "issubclass() arg 1 must be a class"), []),
    (("TypeError", "issubclass() arg 2 must be " + arg2), bases("D")),
    (("TypeError", "isinstance() arg 2 must be a type, a tuple of types, or a union"), []),
    (False, bases("D")),
    (True, ["class", "class"] + bases("C") + ["class"] + bases("D")),
]

def inside():
    for _ in range(1): pass
    return [run(*case) for case in cases]

def starred(f, *args):
    for _ in range(1): pass
    return f(*args)

assert_eq(inside(), expected)
assert_eq([run(*case) for case in cases], expected)
assert_eq([run(starred, *case) for case in cases], expected)

# Searching several bases deeper than the recursion limit raises.
class Loop:
    @property
    def __bases__(self): return (self, self)
try:
    issubclass(Loop(), int)
    raise AssertionError("no RecursionError")
except RecursionError:
    pass
