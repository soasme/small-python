# spec: PLS-315 25.4, 13.3.3
# description: slice objects, their comparison and hashing, and SliceIndices.
from harness import *

s = slice(5)
assert_eq((s.start, s.stop, s.step), (None, 5, None))
s = slice(1, "x", [])
assert_eq((s.start, s.stop, s.step), (1, "x", []))
assert_raises(AttributeError, setattr, s, "start", 0)
assert_eq(repr(slice(1, 2, 3)), "slice(1, 2, 3)")
assert_eq(repr(slice(None)), "slice(None, None, None)")
e = assert_raises(TypeError, slice)
assert_eq(str(e), "slice expected at least 1 argument, got 0")
e = assert_raises(TypeError, slice, 1, 2, 3, 4)
assert_eq(str(e), "slice expected at most 3 arguments, got 4")
assert_eq(slice(1, 2), slice(1, 2))
assert_true(slice(1, 2) < slice(1, 3))
assert_eq(hash(slice(1, 2)), hash(slice(1, 2)))
assert_raises(TypeError, hash, slice([], 1))
assert_eq(repr(slice[int]), "slice[int]")

assert_eq(slice(None).indices(5), (0, 5, 1))
assert_eq(slice(None, None, -1).indices(5), (4, -1, -1))
assert_eq(slice(-2, None).indices(5), (3, 5, 1))
assert_eq(slice(-100, 100).indices(5), (0, 5, 1))
assert_eq(slice(100, -100, -1).indices(5), (4, -1, -1))
assert_eq(slice(1, 4, 2).indices(10), (1, 4, 2))
assert_eq(slice(10, 0, -3).indices(5), (4, 0, -3))
e = assert_raises(ValueError, slice(None, None, 0).indices, 5)
assert_eq(str(e), "slice step cannot be zero")
e = assert_raises(ValueError, slice(None).indices, -1)
assert_eq(str(e), "length should not be negative")
e = assert_raises(TypeError, slice("a").indices, 5)
assert_eq(str(e), "slice indices must be integers or None or have an __index__ method")
class Index:
    def __index__(self):
        return 2
assert_eq(slice(Index()).indices(5), (0, 2, 1))
assert_eq(slice(None).indices(Index()), (0, 2, 1))

data = list(range(10))
assert_eq(data[slice(2, 8, 3)], [2, 5])
assert_eq(data[::-3], [9, 6, 3, 0])
e = assert_raises(TypeError, data.__getitem__, slice("a", None))
assert_eq(str(e), "slice indices must be integers or have an __index__ method")
assert_eq(data[-(1 << 100):1 << 100], data)
assert_eq("abcdef"[Index():], "cdef")
