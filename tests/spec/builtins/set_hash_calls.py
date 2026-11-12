# spec: PLS-315 26.3.1, 13.2.2, 26
# description: set(), frozenset() and a set display's starred item call
# each element's Python __hash__ as they take it, before the next item
# is taken, from a list, a tuple, a generator or an instance; an equal
# element already present is kept; a TypeError from __hash__ is named as
# a set element's, any other exception propagates.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class K:
    def __init__(self, v): self.v = v
    def __hash__(self):
        spin(); log.append("h%d" % self.v)
        return self.v
    def __eq__(self, other): return isinstance(other, K) and self.v == other.v
    def __repr__(self): return "K%d" % self.v
class Plain:
    # A body with no call or loop.
    def __init__(self, v): self.v = v
    def __hash__(self): log.append("p"); return self.v
def gen(*items):
    for item in items:
        log.append("y%r" % item)
        yield item
class Items:
    def __init__(self, *items): self.items = items
    def __iter__(self): spin(); return iter(self.items)

k1, k2, again = K(1), K(2), K(1)
def check(make, kind, elements, calls):
    log.clear()
    s = make()
    assert_eq(type(s), kind)
    assert_eq(sorted(s, key=repr), elements)
    assert_eq(log, calls)
    return s

def main():
    check(lambda: set([k1, k2, again]), set, [k1, k2], ["h1", "h2", "h1"])
    check(lambda: frozenset((k1, 3, k2)), frozenset, [3, k1, k2], ["h1", "h2"])
    check(lambda: set(gen(k1, k2)), set, [k1, k2], ["yK1", "h1", "yK2", "h2"])
    check(lambda: frozenset(gen(k2)), frozenset, [k2], ["yK2", "h2"])
    check(lambda: set(Items(k1, k2)), set, [k1, k2], ["h1", "h2"])
    check(lambda: {*[k1, k2]}, set, [k1, k2], ["h1", "h2"])
    check(lambda: {0, *gen(k1), k2}, set, [0, k1, k2], ["yK1", "h1", "h2"])
    check(lambda: {*(k1,), *[again]}, set, [k1], ["h1", "h1"])
    plain = Plain(4)
    check(lambda: set([plain, k1]), set, sorted([plain, k1], key=repr), ["p", "h1"])
    # The element kept is the first of equal ones.
    s = check(lambda: set([k1, again]), set, [k1], ["h1", "h1"])
    assert_true(next(iter(s)) is k1)
    # The items are the set's own: a source changed afterwards is not.
    items = [k1]
    s = set(items)
    items.append(k2)
    assert_eq(s, {k1})
    # A set of plain values calls nothing.
    assert_eq(set([1, 2, 1]), {1, 2})
    def inner():
        return set(gen(k2, k1))
    check(inner, set, [k1, k2], ["yK2", "h2", "yK1", "h1"])
main()

# A failing __hash__ stops the set at that element.
class Wrong:
    def __hash__(self): spin(); return "x"
class Raising:
    def __init__(self, error): self.error = error
    def __hash__(self): spin(); raise self.error
    def __repr__(self): return "R"
class Arity:
    def __hash__(self, extra): spin(); return 1
makers = [lambda x: set([k1, x]), lambda x: frozenset((x,)), lambda x: set(gen(x)), lambda x: {*[x]}, lambda x: {*gen(x)}]
for make in makers:
    assert_raises(TypeError, make, Wrong(), message="cannot use 'Wrong' as a set element (__hash__ method should return an integer)")
    assert_raises(TypeError, make, Raising(TypeError("t")), message="cannot use 'Raising' as a set element (t)")
    assert_raises(ValueError, make, Raising(ValueError("v")), message="v")
    assert_raises(TypeError, make, Arity(), message="cannot use 'Arity' as a set element (Arity.__hash__() missing 1 required positional argument: 'extra')")
log.clear()
assert_raises(ValueError, lambda: set(gen(Raising(ValueError("v")), k1)), message="v")
assert_eq(log, ["yR"])
