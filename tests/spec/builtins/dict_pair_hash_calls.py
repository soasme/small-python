# spec: PLS-315 26.1.1, 27.1.8, 26
# description: dict() and a dict's update of pairs, from a list, a tuple,
# a zip or a generator, set each pair's key to its value before the next
# pair is taken, as they set a mapping's keys to its values, hashing the
# key by its class's Python __hash__, which may loop, and comparing it
# with a present key of the same hash by Python __eq__, the present key's
# first; an equal key keeps its first spelling and takes the later value,
# a set of a zip hashes its tuples' items so, and an error stops the
# update.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class K:
    def __init__(self, v, tag): self.v, self.tag = v, tag
    def __hash__(self): spin(); log.append("h" + self.tag); return self.v
    def __eq__(self, other):
        spin(); log.append(self.tag + getattr(other, "tag", "?"))
        return isinstance(other, K) and other.v == self.v
class Raising:
    def __hash__(self): spin(); raise ValueError("nope")
def gen(*items):
    for item in items:
        log.append("y")
        yield item

def check(expression, value, calls):
    log.clear()
    result = expression()
    assert_eq([(getattr(k, "tag", k), v) for k, v in result.items()], value)
    assert_eq(log, calls)

a, b = K(1, "a"), K(2, "b")
def main():
    check(lambda: dict([(a, 1), (b, 2), (K(1, "c"), 3)]), [("a", 3), ("b", 2)], ["ha", "hb", "hc", "ac"])
    check(lambda: dict(((b, 0), [a, 1])), [("b", 0), ("a", 1)], ["hb", "ha"])
    check(lambda: dict(zip([a, "s", K(1, "d")], (1, 2, 3))), [("a", 3), ("s", 2)], ["ha", "hd", "ad"])
    check(lambda: dict(gen((a, 1), (K(1, "e"), 2))), [("a", 2)], ["y", "ha", "y", "he", "ae"])
    def update():
        d = {b: 0}
        d.update([(K(2, "f"), 5), ("t", 6)])
        d.update(zip((a,), [7]))
        return d
    check(update, [("b", 5), ("t", 6), ("a", 7)], ["hb", "hf", "bf", "ha"])
    def loop():
        return [dict([(k, 0)]) for k in (a, b)]
    log.clear()
    assert_eq([list(d) for d in loop()], [[a], [b]])
    assert_eq(log, ["ha", "hb"])
    class Mapping:
        def __init__(self, keys): self.k = keys
        def keys(self): return self.k
        def __getitem__(self, k): return getattr(k, "tag", k)
    check(lambda: dict(Mapping([a, "u", K(1, "m")])), [("a", "m"), ("u", "u")], ["ha", "hm", "am"])
    first = K(1, "g")
    d = dict([(first, 1), (a, 2)])
    assert_true(next(iter(d)) is first)
    log.clear()
    assert_eq(len(set(zip([a, K(1, "i")]))), 1)
    assert_eq(log, ["ha", "hi", "ai"])
main()

log.clear()
assert_raises(ValueError, lambda: dict([(a, 1), (Raising(), 2), (b, 3)]), message="nope")
assert_eq(log, ["ha"])
assert_raises(TypeError, lambda: dict([(a, 1), ([], 2)]), message="cannot use 'list' as a dict key (unhashable type: 'list')")
assert_raises(ValueError, lambda: dict([(1, 2), (a, 3, 4)]), message="dictionary update sequence element #1 has length 3; 2 is required")
