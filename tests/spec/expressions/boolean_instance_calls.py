# spec: PLS-315 13.11, 7.5.1
# description: and and or of an instance call its class's Python __bool__ (or __len__) once, keep the instance itself as their value, and the test their jump lands on reuses that truth; its errors propagate.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class Truth:
    def __init__(self, name, v): self.name, self.v = name, v
    def __bool__(self):
        spin(); log.append(self.name)
        return self.v
    def __repr__(self): return self.name
class Sized:
    def __init__(self, name, n): self.name, self.n = name, n
    def __len__(self):
        spin(); log.append(self.name)
        return self.n
class Plain:
    # A body with no call or loop.
    def __init__(self, v): self.v = v
    def __bool__(self): log.append("plain"); return self.v

t, f = Truth("t", True), Truth("f", False)
def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    check(lambda: f and 1, f, ["f"])
    check(lambda: t and 1, 1, ["t"])
    check(lambda: t or 1, t, ["t"])
    check(lambda: f or 1, 1, ["f"])
    check(lambda: f or t, t, ["f"])
    check(lambda: t and f and 1, f, ["t", "f"])
    check(lambda: f or f or t, t, ["f", "f"])
    check(lambda: (f and 1) or 2, 2, ["f"])
    check(lambda: not (t and f), True, ["t", "f"])
    check(lambda: Sized("s", 0) or 3, 3, ["s"])
    check(lambda: Sized("s", 2) and 3, 3, ["s"])
    check(lambda: Plain(False) or 4, 4, ["plain"])
    # The test the jump lands on takes the same truth: one call each.
    def tested(x, y):
        if x and y: return "both"
        return "not"
    check(lambda: tested(f, t), "not", ["f"])
    check(lambda: tested(t, f), "not", ["t", "f"])
    check(lambda: tested(t, t), "both", ["t", "t"])
    def either(x, y):
        if x or y: return "one"
        return "none"
    check(lambda: either(t, f), "one", ["t"])
    check(lambda: either(f, f), "none", ["f", "f"])
    def counting(x):
        n = 0
        while x and n < 2: n += 1
        return n
    check(lambda: counting(t), 2, ["t", "t", "t"])
    check(lambda: [v for v in (t, f) if v and True], [t], ["t", "f"])
    def gen():
        yield f or t
    check(lambda: list(gen()), [t], ["f"])
main()

# A __bool__ returning a non-bool, or raising, propagates its error.
class Wrong:
    def __bool__(self): spin(); return 1
class Raising:
    def __bool__(self): spin(); raise KeyError("k")
assert_raises(TypeError, lambda: Wrong() and 1, message="Wrong.__bool__() must return a bool, not int")
assert_raises(TypeError, lambda: Wrong() or 1, message="Wrong.__bool__() must return a bool, not int")
assert_raises(KeyError, lambda: Raising() or 1, message="'k'")
class Negative:
    def __len__(self): spin(); return -1
assert_raises(ValueError, lambda: Negative() and 1, message="__len__() should return >= 0")
