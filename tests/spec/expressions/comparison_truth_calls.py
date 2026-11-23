# spec: PLS-315 7.5.1, 13.10
# description: a comparison whose result an if, a while, an assert or a
# chain tests calls the result's Python __bool__, or __len__ when it has
# none, once, each of which may loop: a chain goes on to its next
# comparison when it is true, else its value is the false result; a
# __bool__ returning other than a bool is a TypeError naming the class,
# and an exception from either propagates. Reflected comparisons, and
# inside functions as at module level.
from harness import *

log = []

class Truth:
    def __init__(self, v): self.v = v
    def __bool__(self):
        for _ in (): pass
        log.append(("bool", self.v))
        if self.v is None: raise LookupError("bool")
        return self.v

class Sized:
    def __init__(self, n): self.n = n
    def __len__(self):
        for _ in (): pass
        log.append(("len", self.n))
        return self.n

class V:
    def __init__(self, r): self.r = r
    def __lt__(self, o): return self.r
    def __gt__(self, o): return self.r

def tests():
    out = []
    if V(Truth(True)) < 1: out.append("if")
    if V(Truth(False)) < 1: out.append("no")
    else: out.append("else")
    if 1 > V(Sized(2)): out.append("reflected")
    n = 0
    while V(Sized(1 - n)) < 1: n += 1
    out.append(n)
    assert V(Truth(True)) < 1
    out.append(V(Truth(True)) < 1 < 2)
    out.append((V(Truth(False)) < 1 < 2).v)
    out.append((V(Sized(0)) < 1 < 2).n)
    out.append((1 < 2 < V(Truth(True)) < 3).v)
    return out

expected = ["if", "else", "reflected", 1, True, False, 0, True]
expected_log = [("bool", True), ("bool", False), ("len", 2), ("len", 1), ("len", 0), ("bool", True), ("bool", True),
                ("bool", False), ("len", 0), ("bool", True)]
assert_eq(tests(), expected)
assert_eq(log, expected_log)
log.clear()

if V(Truth(True)) < 1: log.append("module")
assert_eq(V(Sized(3)) < 1 < 5, True)
assert_eq(log, [("bool", True), "module", ("len", 3)])

def errors():
    out = []
    for make in (lambda: V(Truth(None)) < 1 < 2, lambda: V(Truth(1)) < 1 < 2, lambda: V(Sized(-1)) < 1 < 2):
        try: make()
        except LookupError as e: out.append(e.args)
        except (TypeError, ValueError) as e: out.append(str(e))
    try:
        if V(Truth(2)) < 1: pass
    except TypeError as e: out.append(str(e))
    return out

assert_eq(errors(), [("bool",), "Truth.__bool__() must return a bool, not int", "__len__() should return >= 0",
                     "Truth.__bool__() must return a bool, not int"])

# A chain's truth test of a comparison's result calls its __len__, whose
# result's Python __index__ gives the length; a __bool__ whose descriptor
# raises AttributeError leaves __len__ to decide.
class ChainIndex:
    def __init__(self, n): self.n = n
    def __index__(self): return self.n
class ChainSized:
    def __init__(self, n): self.n = n
    def __len__(self): return ChainIndex(self.n)
    def __repr__(self): return "ChainSized(%d)" % self.n
class ChainMissingBool:
    def __get__(self, obj, cls): raise AttributeError("no bool")
class ChainBehind:
    __bool__ = ChainMissingBool()
    def __init__(self, n): self.n = n
    def __len__(self): return self.n
    def __repr__(self): return "ChainBehind(%d)" % self.n
class ChainLess:
    def __init__(self, result): self.result = result
    def __lt__(self, other): return self.result
chained = [ChainLess(ChainSized(1)) < ChainLess("end") < "end", ChainLess(ChainSized(0)) < ChainLess("end") < "end",
           ChainLess(ChainBehind(2)) < ChainLess("end") < "end", ChainLess(ChainBehind(0)) < ChainLess("end") < "end"]
assert_eq(repr(chained), repr(["end", ChainSized(0), "end", ChainBehind(0)]))
