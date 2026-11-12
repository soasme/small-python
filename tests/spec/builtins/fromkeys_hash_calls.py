# spec: PLS-315 26.1.1, 7.5.7
# description: dict.fromkeys sets each element of its iterable, a list, a
# tuple, an iterator or a generator, to the value, None by default, before
# it takes the next, hashing an element by its class's Python __hash__,
# which may loop; an equal key keeps its first spelling, and a hash that
# fails names the key as a dict key's.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class K:
    def __init__(self, v): self.v = v
    def __hash__(self): spin(); log.append("h%d" % self.v); return self.v
    def __eq__(self, other): log.append("e"); return isinstance(other, K) and other.v == self.v
class Raising:
    def __hash__(self): spin(); raise TypeError("nope")
class Wrong:
    def __hash__(self): spin(); return "x"
def gen(*items):
    for item in items:
        log.append("y")
        yield item

a, b = K(1), K(2)
def check(expression, value, calls):
    log.clear()
    result = expression()
    assert_eq([(type(k).__name__, getattr(k, "v", k), v) for k, v in result.items()], value)
    assert_eq(log, calls)

def main():
    check(lambda: dict.fromkeys([a, 3, b]), [("K", 1, None), ("int", 3, None), ("K", 2, None)], ["h1", "h2"])
    check(lambda: dict.fromkeys((b, a), 0), [("K", 2, 0), ("K", 1, 0)], ["h2", "h1"])
    check(lambda: dict.fromkeys(gen(a, b), "v"), [("K", 1, "v"), ("K", 2, "v")], ["y", "h1", "y", "h2"])
    check(lambda: dict.fromkeys(iter([b])), [("K", 2, None)], ["h2"])
    check(lambda: {}.fromkeys([a]), [("K", 1, None)], ["h1"])
    check(lambda: dict.fromkeys([a, a]), [("K", 1, None)], ["h1", "h1"])
    first = K(1)
    check(lambda: dict.fromkeys([first, a], 5), [("K", 1, 5)], ["h1", "h1", "e"])
    log.clear()
    assert_true(next(iter(dict.fromkeys([first, a]))) is first)
    shared = []
    d = dict.fromkeys([a, b], shared)
    assert_true(d[a] is shared and d[b] is shared)
    assert_eq(type(dict.fromkeys([a])), dict)
main()

assert_raises(TypeError, lambda: dict.fromkeys([Raising()]), message="cannot use 'Raising' as a dict key (nope)")
assert_raises(TypeError, lambda: dict.fromkeys([a, Wrong()]),
              message="cannot use 'Wrong' as a dict key (__hash__ method should return an integer)")
assert_raises(TypeError, lambda: dict.fromkeys([[1], a]), message="cannot use 'list' as a dict key (unhashable type: 'list')")
log.clear()
assert_raises(TypeError, lambda: dict.fromkeys(gen(a, Raising(), b)), message="cannot use 'Raising' as a dict key (nope)")
assert_eq(log, ["y", "h1", "y"])
