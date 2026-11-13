# spec: PLS-315 26.3.1, 26.3.2, 26.1.1, 25.2
# description: set(), frozenset(), a set's update, a set display's starred
# list and dict.fromkeys hash each tuple element as they take it, calling
# Hash of its items in order, nested tuples depth first, by Python
# __hash__ methods that may loop, before the next element is taken; a
# tuple keeps its hash, and an item's error or an unhashable item stops
# the build with the set's TypeError.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class K:
    def __init__(self, v): self.v = v
    def __hash__(self): spin(); log.append(self.v); return self.v
    def __eq__(self, other): return isinstance(other, K) and other.v == self.v

def check(make, size, calls):
    log.clear()
    assert_eq(len(make()), size)
    assert_eq(log, calls)

def main():
    a, b = K(1), K(2)
    kept = (a, (b, 3))
    check(lambda: set([(a,), (1, (b,)), (a,)]), 2, [1, 2, 1])
    check(lambda: frozenset(((a, 2), kept, kept)), 2, [1, 1, 2])
    check(lambda: set([kept]), 1, [])
    def update():
        s = {0}
        s.update([(b,), (b, a)])
        return s
    check(update, 3, [2, 2, 1])
    check(lambda: dict.fromkeys([(a,), 3, (a,)], 0), 2, [1, 1])
    check(lambda: {*[(a, b), "x"]}, 2, [1, 2])
    def gen():
        log.append("y"); yield (a,)
        log.append("y"); yield (b,)
    check(lambda: set(gen()), 2, ["y", 1, "y", 2])
main()

class Raising:
    def __hash__(self): spin(); log.append("r"); raise ValueError("r")
a = K(1)
log.clear()
assert_raises(ValueError, lambda: set([(a, Raising()), (K(9),)]), message="r")
assert_eq(log, [1, "r"])
assert_raises(TypeError, lambda: frozenset([(a, [])]), message="cannot use 'tuple' as a set element (unhashable type: 'list')")
assert_raises(TypeError, lambda: dict.fromkeys([([], a)]), message="cannot use 'tuple' as a dict key (unhashable type: 'list')")
