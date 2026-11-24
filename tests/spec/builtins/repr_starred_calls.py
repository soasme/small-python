# spec: PLS-315 19.3.32, 19.3.5, 19.3.16
# description: repr(), str() and ascii() of a container, called through a
# starred call, and format() of one with an empty spec, an exact str or a
# str subclass, plain or starred, call each item's Python __repr__, which
# may loop, in order; an error from one propagates, and a non-empty spec
# is refused by the container's __format__.
from harness import *

log = []
class R:
    def __init__(self, name): self.name = name
    def __repr__(self):
        for _ in range(2): pass
        log.append(self.name); return "R" + self.name
class Bad:
    def __repr__(self):
        for _ in range(2): pass
        raise ValueError("bad")
class Spec(str): pass
def call(function, *args, **kwargs): return function(*args, **kwargs)

def check(expression, text, calls):
    log.clear()
    assert_eq(expression(), text)
    assert_eq(log, calls)

def main():
    check(lambda: call(repr, [R("a"), R("b")]), "[Ra, Rb]", ["a", "b"])
    check(lambda: call(str, (R("c"),)), "(Rc,)", ["c"])
    check(lambda: call(ascii, ["\xe9", R("d")]), "['\\xe9', Rd]", ["d"])
    check(lambda: call(repr, {1: R("e")}), "{1: Re}", ["e"])
    check(lambda: call(format, [R("f")]), "[Rf]", ["f"])
    check(lambda: format([R("g")], ""), "[Rg]", ["g"])
    check(lambda: call(format, [R("h")], ""), "[Rh]", ["h"])
    check(lambda: format([R("i")], Spec("")), "[Ri]", ["i"])
main()

assert_raises(ValueError, lambda: call(repr, [Bad()]), message="bad")
assert_raises(ValueError, lambda: format([Bad()], ""), message="bad")
assert_raises(TypeError, lambda: format([R("x")], "x"), message="unsupported format string passed to list.__format__")
