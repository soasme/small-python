# spec: PLS-315 19.3.5, 7.5.6
# description: ascii() of a list, tuple, dict or set whose items, at any
# depth, have a Python __repr__, which may loop, calls each in order and
# escapes the whole repr's non-ASCII characters; a non-str __repr__ result
# is a TypeError, and a recursive container shows [...]. Inside functions
# and generators as at module level.
from harness import *

log = []

class Shown:
    def __init__(self, t): self.t = t
    def __repr__(self):
        for _ in (): pass
        log.append(self.t)
        return self.t

def calls():
    return [ascii([Shown("x")]), ascii((Shown("\xe9"), [Shown("\u20ac")], {"k": Shown("\xfc")})), ascii({Shown("s")})]

assert_eq(calls(), ["[x]", "(\\xe9, [\\u20ac], {'k': \\xfc})", "{s}"])
assert_eq(log, ["x", "\xe9", "\u20ac", "\xfc", "s"])
log.clear()

def errors():
    try: ascii([[Shown(3)]])
    except TypeError as e: return str(e)

assert_eq(errors(), "Shown.__repr__() must return a str, not int")
l = [1]; l.append(l)
assert_eq(ascii([Shown("\xe9"), l]), "[\\xe9, [1, [...]]]")

def gen(): yield ascii([Shown("\u015d")])

assert_eq(list(gen()), ["[\\u015d]"])
assert_eq(log, [3, "\xe9", "\u015d"])
# A __repr__, Python or native, returning an int is a TypeError however
# ascii() is reached.
class ReprInt:
    def __repr__(self): return 5
class NativeReprInt:
    __repr__ = (5).__index__
def repr_ints():
    out = []
    for f in (lambda: ascii(ReprInt()), lambda: "%a" % ReprInt(), lambda: f"{ReprInt()!a}", lambda: list(map(ascii, [ReprInt()])),
              lambda: ascii(NativeReprInt()), lambda: "%a" % (NativeReprInt(),), lambda: list(map(ascii, [NativeReprInt()])),
              lambda: ascii([ReprInt()])):
        try: out.append(f())
        except TypeError as e: out.append(str(e))
    return out
assert_eq(repr_ints(), ["ReprInt.__repr__() must return a str, not int"] * 4 + ["NativeReprInt.__repr__() must return a str, not int"] * 3
          + ["ReprInt.__repr__() must return a str, not int"])
