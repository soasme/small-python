# spec: PLS-315 27.1.7
# description: reversed() of an instance whose class has __getitem__ and no
# __reversed__ calls its __len__, which may call others or not, once, and
# iterates from the length down; a negative, oversized or non-integer length
# raises, as does an exception from __len__ or a missing __len__, while a
# None __reversed__ or a dict subclass is not reversible; map(reversed, ...)
# calls each item's; inside functions as at module level.
from harness import *

log = []

class Seq:
    def __init__(self, n): self.n = n
    def __len__(self):
        log.append(("len", self.n))
        for _ in range(1): pass
        if self.n == "boom": raise KeyError("k")
        return self.n
    def __getitem__(self, i):
        if i >= 3: raise IndexError(i)
        return i * 10

class Quick(Seq):
    def __len__(self):
        log.append(("len", self.n))
        return self.n

def items(it):
    return [x for x in it]

class NoLen:
    def __getitem__(self, i): return i

class Refused(Seq):
    __reversed__ = None

class Mapping(dict):
    def __len__(self): return 1

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def calls():
    del log[:]
    out = [items(reversed(Seq(3))), items(reversed(Seq(0))), items(reversed(Quick(2))), items(reversed(Seq(5)))]
    out.append(error(lambda: reversed(Seq(-1))))
    out.append(error(lambda: reversed(Seq(2**70))))
    out.append(error(lambda: reversed(Seq(1.5))))
    out.append(error(lambda: reversed(Seq("boom"))))
    out.append(error(lambda: reversed(NoLen())))
    out.append(error(lambda: reversed(Refused(1))))
    out.append(type(reversed(Mapping())).__name__)
    out.append([next(r) for r in map(reversed, [Seq(3), Quick(1)])])
    out.append(list(log))
    return out

expected = [[20, 10, 0], [], [10, 0], [],
            ("ValueError", "__len__() should return >= 0"),
            ("OverflowError", "cannot fit 'int' into an index-sized integer"),
            ("TypeError", "'float' object cannot be interpreted as an integer"),
            ("KeyError", "'k'"), ("TypeError", "object of type 'NoLen' has no len()"),
            ("TypeError", "'Refused' object is not reversible"), "dict_reversekeyiterator", [20, 0],
            [("len", 3), ("len", 0), ("len", 2), ("len", 5), ("len", -1), ("len", 2**70), ("len", 1.5), ("len", "boom"), ("len", 3), ("len", 1)]]
assert_eq(calls(), expected)
assert_eq(calls(), expected)
log.clear()
assert_eq([items(reversed(Seq(2))), error(lambda: reversed(Seq(-2)))], [[10, 0], ("ValueError", "__len__() should return >= 0")])
assert_eq(log, [("len", 2), ("len", -2)])
