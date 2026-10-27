# spec: PLS-315 10.1.2, 22.4, 23.3.2, 25.1, 26.1.4, 29.9.1
# description: list method arguments, empty slots, complex powers, dict mutation during iteration, and lazy error handlers.
from harness import *

l = [1, 2, 3]
for key in (slice(1, 2), slice(None, None, 2)):
    e = assert_raises(TypeError, l.__setitem__, key, 5)
    assert_eq(str(e), "must assign iterable to extended slice")
assert_eq(str(assert_raises(TypeError, l.sort, cmp=1)), "sort() got an unexpected keyword argument 'cmp'")
for args in ((1, "a"), (1, 0, "a"), (1, None)):
    assert_eq(str(assert_raises(TypeError, l.index, *args)), "slice indices must be integers or have an __index__ method")
assert_eq(str(assert_raises(TypeError, (1, 2).index, 1, 1.5)), "slice indices must be integers or have an __index__ method")

class Outer:
    class Slotted:
        __slots__ = ("a",)
e = assert_raises(AttributeError, getattr, Outer.Slotted(), "a")
assert_eq(str(e), "'Outer.Slotted' object has no attribute 'a'")
e = assert_raises(AttributeError, delattr, Outer.Slotted(), "a")
assert_eq(e.args, ("a",))

assert_eq(str(assert_raises(OverflowError, round, 1.7976931348623157e308, -308)), "rounded value too large to represent")
inf = float("inf")
for base, exponent in ((1e300 + 1e300j, 2), (2 + 0j, 2000), (complex(inf, 0), 2), (complex(inf, 0), 0.5), (1 + 1j, 1e10)):
    assert_eq(str(assert_raises(OverflowError, pow, base, exponent)), "complex exponentiation")
for base, exponent in ((1e-300 + 0j, -2), (0j, -1), (0j, 1j)):
    assert_eq(str(assert_raises(ZeroDivisionError, pow, base, exponent)), "zero to a negative or complex power")
assert_eq(repr((2 + 0j) ** complex(inf, 0)), "(nan+nanj)")
assert_eq((2 + 1j) ** 2, 3 + 4j)

def mutate(d, change):
    for k in d:
        change(d, k)
d = {1: 1, 2: 2}
e = assert_raises(RuntimeError, mutate, d, lambda d, k: (d.pop(k), d.__setitem__(k + 10, 1)))
assert_eq(str(e), "dictionary keys changed during iteration")
mutate({1: 1, 2: 2}, lambda d, k: d.__setitem__(k, 5))

assert_eq("a".encode(errors="nope"), b"a")
assert_eq(str(b"a", errors="nope"), "a")
assert_eq(str(assert_raises(LookupError, b"\xff".decode, "utf-8", "nope")), "unknown error handler name 'nope'")
assert_eq(str(assert_raises(LookupError, "\udc80".encode, "utf-8", "nope")), "unknown error handler name 'nope'")
e = assert_raises(TypeError, b"\xff".decode, "utf-8", "xmlcharrefreplace")
assert_eq(str(e), "don't know how to handle UnicodeDecodeError in error callback")

GenericAlias = type(list[int])
assert_eq(str(assert_raises(TypeError, GenericAlias, list)), "GenericAlias expected 2 arguments, got 1")
assert_eq(str(assert_raises(TypeError, GenericAlias, list, int, x=1)), "GenericAlias() takes no keyword arguments")
