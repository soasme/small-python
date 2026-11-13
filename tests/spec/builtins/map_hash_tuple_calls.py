# spec: PLS-315 27.1.6, 19.3.18, 25.2
# description: map(hash, ...) hashes each tuple item as the map gives it,
# calling Hash of the tuple's items in order, nested tuples depth first,
# by Python __hash__ methods that may loop, whether a loop, a consumer or
# a generator's yield from takes the map; an item's error propagates.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class K:
    def __init__(self, v): self.v = v
    def __hash__(self): spin(); log.append(self.v); return self.v

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    check(lambda: list(map(hash, [(K(1),), (2, (K(3), K(4))), "s"])), [hash((1,)), hash((2, (3, 4))), hash("s")], [1, 3, 4])
    def loop():
        out = []
        for h in map(hash, [(K(5),), (K(6), 7)]):
            out.append(h)
            log.append("x")
        return out
    check(loop, [hash((5,)), hash((6, 7))], [5, "x", 6, "x"])
    check(lambda: (sorted(map(hash, [(K(8),)])), sum(map(hash, [(K(9),)]))), ([hash((8,))], hash((9,))), [8, 9])
    def gen():
        yield from map(hash, [(K(10),)])
    check(lambda: list(gen()), [hash((10,))], [10])
    kept = (K(11),)
    check(lambda: list(map(hash, [kept, kept])), [hash((11,))] * 2, [11])
main()

class Raising:
    def __hash__(self): spin(); log.append("r"); raise ValueError("r")
log.clear()
assert_raises(ValueError, lambda: list(map(hash, [(K(1), Raising(), K(2))])), message="r")
assert_eq(log, [1, "r"])
assert_raises(TypeError, lambda: list(map(hash, [(K(1), [])])), message="unhashable type: 'list'")
