# spec: PLS-315 19.3.3, 7.5.1
# description: any() and all() take each item's truth by its class's
# Python __bool__, or __len__, as they take it, from a list, a tuple, a
# dict, an iterator, a generator or an instance, and request no item after
# the deciding one; a truth that cannot be one, or a raising method,
# propagates its error.
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
def gen(*items):
    for item in items:
        log.append("y%r" % item)
        yield item
class Items:
    def __init__(self, *items): self.items = items
    def __iter__(self): spin(); return iter(self.items)

t, f = Truth("t", True), Truth("f", False)
def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    check(lambda: any([f, f, t, f]), True, ["f", "f", "t"])
    check(lambda: all([t, t, f, t]), False, ["t", "t", "f"])
    check(lambda: any((f, f)), False, ["f", "f"])
    check(lambda: all((t,)), True, ["t"])
    check(lambda: any([0, "", t]), True, ["t"])
    check(lambda: all([1, t, 0, f]), False, ["t"])
    check(lambda: any([f, Sized("s", 2), t]), True, ["f", "s"])
    check(lambda: all([Sized("z", 0), t]), False, ["z"])
    check(lambda: any({f: 1, t: 2}), True, ["f", "t"])
    check(lambda: all(iter([t, f, t])), False, ["t", "f"])
    check(lambda: any(gen(f, t, f)), True, ["yf", "f", "yt", "t"])
    check(lambda: all(gen(t, f, t)), False, ["yt", "t", "yf", "f"])
    check(lambda: any(x for x in [f, t]), True, ["f", "t"])
    check(lambda: all(Items(t, f)), False, ["t", "f"])
    check(lambda: any([Plain(False), f]), False, ["plain", "f"])
    check(lambda: all([t] * 3), True, ["t", "t", "t"])
    check(lambda: any([]) or all([]), True, [])
    check(lambda: sum([any([f, t]), all([t, f])]), 1, ["f", "t", "t", "f"])
    def inner():
        yield any([f, t])
        yield all((t, f))
    check(lambda: list(inner()), [True, False], ["f", "t", "t", "f"])
main()

# A __bool__ returning a non-bool, a __len__ that cannot be a length, or
# a raising method, stops at that item with its error.
class Wrong:
    def __bool__(self): spin(); return 1
class Negative:
    def __len__(self): spin(); return -1
class Text:
    def __len__(self): spin(); return "x"
class Raising:
    def __bool__(self): spin(); log.append("r"); raise KeyError("k")
class Arity:
    def __bool__(self, extra): spin(); return True
class LengthArity:
    def __len__(self, extra): spin(); return 1
for make in [lambda x: any([x]), lambda x: all((t, x)), lambda x: any(gen(x)), lambda x: all(iter([x]))]:
    assert_raises(TypeError, make, Wrong(), message="Wrong.__bool__() must return a bool, not int")
    assert_raises(ValueError, make, Negative(), message="__len__() should return >= 0")
    assert_raises(TypeError, make, Text(), message="'str' object cannot be interpreted as an integer")
    assert_raises(KeyError, make, Raising(), message="'k'")
    assert_raises(TypeError, make, Arity(), message="Arity.__bool__() missing 1 required positional argument: 'extra'")
    assert_raises(TypeError, make, LengthArity(), message="LengthArity.__len__() missing 1 required positional argument: 'extra'")
log.clear()
assert_raises(KeyError, lambda: any([Raising(), t]), message="'k'")
assert_eq(log, ["r"])
