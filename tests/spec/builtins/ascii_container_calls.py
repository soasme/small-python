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
