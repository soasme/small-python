# spec: PLS-315 24.4.2
# description: Multi-dimensional memoryviews: item access, slicing along the first dimension, byte orders, and the operations that raise NotImplementedError.
from harness import *

m = memoryview(bytearray(range(12))).cast('B', (3, 4))
assert_eq((m.ndim, m.shape, m.strides, len(m)), (2, (3, 4), (4, 1), 3))
assert_eq((m[1, 2], m[-1, -1]), (6, 11))
assert_eq(m.tolist(), [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]])
m[1, 2] = 99
assert_eq(m.cast('B').tolist()[6], 99)
m[1, 2] = 6

# Byte orders.
assert_eq(m.tobytes(), bytes(range(12)))
assert_eq(m.tobytes('A'), bytes(range(12)))
assert_eq(m.tobytes('F'), bytes([0, 4, 8, 1, 5, 9, 2, 6, 10, 3, 7, 11]))
assert_eq(m[::2].tobytes('A'), bytes([0, 1, 2, 3, 8, 9, 10, 11]))
assert_eq(m[::2].tobytes('F'), bytes([0, 8, 1, 9, 2, 10, 3, 11]))
assert_eq(m[::-1].tobytes('F'), bytes([8, 4, 0, 9, 5, 1, 10, 6, 2, 11, 7, 3]))
assert_eq(m[::-1].tolist()[0], [8, 9, 10, 11])
data = bytearray(24)
flat = memoryview(data).cast('h')
for i in range(12):
    flat[i] = i
h = memoryview(data).cast('B').cast('h', (2, 3, 2))
assert_eq(h[1, 2, 1], 11)
assert_eq(memoryview(h.tobytes('F')).cast('h').tolist(), [0, 6, 2, 8, 4, 10, 1, 7, 3, 9, 5, 11])
assert_eq(str(assert_raises(ValueError, m.tobytes, 'X')), "order must be 'C', 'F' or 'A'")

# Slices select along the first dimension.
assert_eq((m[0:2].shape, m[::2].c_contiguous, m.c_contiguous, m.f_contiguous), ((2, 4), False, True, False))

# The operations CPython leaves unimplemented.
def message(f):
    return str(assert_raises(NotImplementedError, f))
def store(k, v):
    m[k] = v
assert_eq(message(lambda: m[0]), "multi-dimensional sub-views are not implemented")
assert_eq(message(lambda: list(m)), "multi-dimensional sub-views are not implemented")
assert_eq(message(lambda: m.count(1)), "multi-dimensional sub-views are not implemented")
assert_eq(message(lambda: m.index(1)), "multi-dimensional lookup is not implemented")
assert_eq(message(lambda: m[0:1, 0:2]), "multi-dimensional slicing is not implemented")
assert_eq(message(lambda: h[1, 2]), "sub-views are not implemented")
assert_eq(message(lambda: store(0, 1)), "sub-views are not implemented")
assert_eq(message(lambda: store(slice(0, 1), b"1234")), "memoryview slice assignments are currently restricted to ndim = 1")
assert_eq(message(lambda: store((slice(0, 1), slice(0, 1)), b"1")), "memoryview slice assignments are currently restricted to ndim = 1")
e = assert_raises(TypeError, lambda: m[1, 2, 3])
assert_eq(str(e), "cannot index 2-dimension view with 3-element tuple")
