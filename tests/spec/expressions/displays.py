# spec: PLS-315 13.2
# description: List, set, tuple, and dictionary displays including unpacking.
from harness import *

assert_eq([1, 2, 3,], [1, 2, 3])
assert_eq([*range(3), *"ab", 9], [0, 1, 2, "a", "b", 9])
assert_eq([], list())
assert_eq({1, 2, 2, 3}, {3, 2, 1})
assert_type({1}, set)
assert_type({}, dict)
assert_eq({*[1, 2], *{3}}, {1, 2, 3})
assert_eq((*[1], *(2, 3)), (1, 2, 3))
assert_eq((*[],), ())
assert_syntax_error("*a")
assert_syntax_error("(*a)")
assert_compiles("*a,")

# Dictionaries: later keys win, keys evaluated before values, ** merges.
assert_eq({"a": 1, "a": 2}, {"a": 2})
assert_eq({**{"a": 1, "b": 2}, "b": 3, **{"c": 4}}, {"a": 1, "b": 3, "c": 4})
order = []
def k(x):
    order.append(x)
    return x
{k(1): k(2), k(3): k(4)}
assert_eq(order, [1, 2, 3, 4])
assert_raises(TypeError, lambda: {[]: 1})
assert_raises(TypeError, lambda: {[1]})
assert_raises(TypeError, lambda: {**[1]})
assert_eq(list({"x": 1, "y": 2, "x": 3}), ["x", "y"])  # insertion order kept, first position wins
# Equal keys of different types: the first key object is kept.
d = {1: "a", 1.0: "b", True: "c"}
assert_eq(d, {1: "c"})
assert_same(list(d)[0], 1)

# Set displays evaluate left to right; duplicates keep the first element.
s = {1, 1.0, True}
assert_eq(len(s), 1)
assert_same(next(iter(s)), 1)
# ** needs a mapping; keys() must return an iterable.
e = assert_raises(TypeError, lambda: {**5})
assert_eq(str(e), "'int' object is not a mapping")
class BadKeys:
    def keys(self): return 5
    def __getitem__(self, k): return k
e = assert_raises(TypeError, lambda: {**BadKeys()})
assert_eq(str(e), "BadKeys.keys() must return an iterable, not int")
