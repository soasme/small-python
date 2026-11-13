# spec: PLS-315 19.3.18, 25.2, 7.5.7
# description: hash() of a tuple calls Hash of its items in order, nested
# tuples depth first, each by a Python __hash__ that may loop, and gives
# TupleHash of their hashes; the tuple keeps its hash, so hashing it again
# calls none, while an item's error, an unhashable item or a hash that is
# not an int propagates and keeps none.
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
    t = (K(1), (K(2), 3), "s")
    check(lambda: hash(t), hash((1, (2, 3), "s")), [1, 2])
    check(lambda: hash(t), hash((1, (2, 3), "s")), [])
    check(lambda: [hash((K(4),)), hash((5, K(6)))], [hash((4,)), hash((5, 6))], [4, 6])
    check(lambda: hash((K(-1),)) == hash((-2,)), True, [-1])
    def gen():
        yield hash(((K(7),),))
    check(lambda: list(gen()), [hash(((7,),))], [7])
main()

class Raising:
    def __hash__(self): spin(); log.append("r"); raise ValueError("r")
class Wrong:
    def __hash__(self): spin(); return 1.5
log.clear()
bad = (K(1), Raising())
assert_raises(ValueError, lambda: hash(bad), message="r")
assert_raises(ValueError, lambda: hash(bad), message="r")
assert_eq(log, [1, "r", 1, "r"])
assert_raises(TypeError, lambda: hash((K(1), [])), message="unhashable type: 'list'")
assert_raises(TypeError, lambda: hash(([], K(1))), message="unhashable type: 'list'")
assert_raises(TypeError, lambda: hash((1, (Wrong(),))), message="__hash__ method should return an integer")
