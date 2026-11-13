# spec: PLS-315 26.3.2, 26.3.1, 7.5.7
# description: set.update adds each element of its iterable, a list, a
# tuple, an iterator or a generator, by SetAdd before it takes the next,
# hashing an element by its class's Python __hash__, which may loop; an
# equal element keeps the present one, a set subclass and a bound method
# update the same way, and a hash that fails names the element as a set
# element's, the elements before it kept.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class K:
    def __init__(self, v): self.v = v
    def __hash__(self): spin(); log.append("h%d" % self.v); return self.v
    def __eq__(self, other): return isinstance(other, K) and other.v == self.v
class Raising:
    def __hash__(self): spin(); log.append("raise"); raise TypeError("nope")
class Sub(set): pass
def gen(*items):
    for item in items:
        log.append("y")
        yield item
def values(s):
    return sorted(getattr(v, "v", v) for v in s)

a, b = K(1), K(2)
def check(source, value, calls, kind=set):
    log.clear()
    s = kind({0})
    assert_eq(s.update(source), None)
    assert_eq(values(s), value)
    assert_eq(log, calls)
    return s

def main():
    check([a, 3, b], [0, 1, 2, 3], ["h1", "h2"])
    check((b, a), [0, 1, 2], ["h2", "h1"])
    check(iter([b]), [0, 2], ["h2"])
    check(gen(a, b), [0, 1, 2], ["y", "h1", "y", "h2"])
    check([a, K(1)], [0, 1], ["h1", "h1"])
    assert_eq(type(check([b], [0, 2], ["h2"], Sub)), Sub)
    log.clear()
    first, s = K(1), set()
    s.update([first])
    s.update([a])
    assert_true(next(iter(s)) is first)
    update = s.update
    update((b,))
    assert_eq(values(s), [1, 2])
main()

log.clear()
s = {0}
assert_raises(TypeError, s.update, [a, Raising(), b], message="cannot use 'Raising' as a set element (nope)")
assert_eq((values(s), log), ([0, 1], ["h1", "raise"]))
assert_raises(TypeError, s.update, [[1], a], message="cannot use 'list' as a set element (unhashable type: 'list')")
