# spec: PLS-315 19.3.21, 19.3.22
# description: isinstance and issubclass of objects that are not classes read
# __bases__ and __class__ through their Python properties and __getattr__
# fallbacks in protocol order, a tuple target trying each item in turn,
# called directly, with starred arguments, by map, or as type's
# __instancecheck__ and __subclasscheck__;
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

# type.__instancecheck__ and __subclasscheck__ called directly, and the
# builtins called by map, follow the same protocol.
class One:
    __bases__ = ()
class Through:
    @property
    def __bases__(self): return (one,)
class Failing:
    @property
    def __bases__(self): raise LookupError("bases")
class Several:
    __bases__ = (One, int)
one = One()
class Claims:
    __class__ = property(lambda self: Through())
class Raises:
    @property
    def __class__(self): raise LookupError("class")
class Missing:
    @property
    def __class__(self): raise AttributeError("class")
class Small(int): pass
class Names:
    __class__ = Small
def checks():
    out = []
    for f, args in ((type.__subclasscheck__, (int, Through())), (type.__subclasscheck__, (int, Several())),
                    (type.__subclasscheck__, (int, 1)), (type.__subclasscheck__, (int, Failing())),
                    (type.__subclasscheck__, (int, Small)), (type.__instancecheck__, (int, Claims())),
                    (type.__instancecheck__, (int, Raises())), (type.__instancecheck__, (int, Missing())),
                    (type.__instancecheck__, (int, Names())), (type.__instancecheck__, (int, 1))):
        try: out.append(f(*args))
        except Exception as e: out.append((type(e).__name__, str(e)))
    out.append(list(map(isinstance, [1, Claims()], [one, one])))
    out.append(list(map(issubclass, [Through()], [one])))
    return out
expected_checks = [False, True, ("TypeError", "issubclass() arg 1 must be a class"), ("LookupError", "bases"), True,
                   False, ("LookupError", "class"), False, True, True, [False, True], [True]]
assert_eq(checks(), expected_checks)
