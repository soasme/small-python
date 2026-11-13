# spec: PLS-315 19.3.34, 25.1.4
# description: sorted() of a set, a frozenset, a dict, a dict's keys or an
# iterator part way through a list takes its items as list() does, then
# sorts them by their Python __lt__ methods, which may loop, reversed or
# not; an error stops the sort. Which comparisons it makes is the
# implementation's.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class K:
    def __init__(self, v): self.v = v
    def __hash__(self): return self.v
    def __lt__(self, other):
        spin(); log.append((self.v, other.v))
        if self.v == 9: raise KeyError(9)
        return self.v < other.v

def check(expression, value):
    log.clear()
    assert_eq([k.v for k in expression()], value)
    assert_eq(len(log) > 0, True)

def main():
    a, b, c = K(3), K(1), K(2)
    check(lambda: sorted({a, b, c}), [1, 2, 3])
    check(lambda: sorted(frozenset([a, b, c]), reverse=True), [3, 2, 1])
    check(lambda: sorted({a: 0, b: 1}), [1, 3])
    check(lambda: sorted({a: 0, b: 1, c: 2}.keys(), reverse=True), [3, 2, 1])
    it = iter([K(5), K(4), K(6)])
    next(it)
    check(lambda: sorted(it), [4, 6])
    def gen():
        yield sorted({b: 0, a: 1})
    check(lambda: next(gen()), [1, 3])
main()

assert_raises(KeyError, lambda: sorted({K(1): 0, K(9): 0}), message="9")
assert_raises(TypeError, lambda: sorted({K(1): 0, 2: 0}))
