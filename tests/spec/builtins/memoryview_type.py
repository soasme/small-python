# spec: PLS-315 24.4
# description: The buffer protocol, __buffer__, and memoryview members.
from harness import *

m = memoryview(b"abcd")
assert_eq((len(m), m[0], m[-1]), (4, 97, 100))
assert_type(m[1:3], memoryview)
assert_eq(m[1:3].tobytes(), b"bc")
assert_eq(m[::2].tolist(), [97, 99])
assert_is(m.obj, m.obj)
assert_eq((m.nbytes, m.readonly, m.itemsize, m.format, m.ndim, m.shape, m.strides, m.suboffsets),
          (4, True, 1, "B", 1, (4,), (1,), ()))
assert_true(m.c_contiguous and m.f_contiguous and m.contiguous)
assert_eq(m.hex(), "61626364")
assert_eq(m.hex(":", 2), "6162:6364")
assert_eq(m, b"abcd")
assert_eq(m, bytearray(b"abcd"))
assert_ne(m, b"abce")
assert_eq(hash(m), hash(b"abcd"))
e = assert_raises(IndexError, m.__getitem__, 9)
assert_eq(str(e), "index out of bounds on dimension 1")
e = assert_raises(TypeError, m.__getitem__, "x")
assert_eq(str(e), "memoryview: invalid slice key")
e = assert_raises(TypeError, m.__setitem__, 0, 1)
assert_eq(str(e), "cannot modify read-only memory")
assert_raises(TypeError, lambda: m < m)

data = bytearray(b"\x01\x00\x02\x00")
w = memoryview(data)
assert_false(w.readonly)
w[0] = 9
assert_eq(data[0], 9)
w[2:4] = b"\x07\x07"
assert_eq(data, bytearray(b"\x09\x00\x07\x07"))
e = assert_raises(ValueError, w.__setitem__, slice(0, 2), b"x")
assert_eq(str(e), "memoryview assignment: lvalue and rvalue have different structures")
e = assert_raises(ValueError, hash, w)
assert_eq(str(e), "cannot hash writable memoryview object")
e = assert_raises(TypeError, w.__setitem__, 0, "x")
assert_eq(str(e), "memoryview: invalid type for format 'B'")
e = assert_raises(ValueError, w.__setitem__, 0, 256)
assert_eq(str(e), "memoryview: invalid value for format 'B'")
r = w.toreadonly()
assert_true(r.readonly)
assert_raises(TypeError, r.__setitem__, 0, 1)

# cast to another format and shape.
c = memoryview(bytearray(8)).cast("i")
assert_eq((len(c), c.itemsize, c.format), (2, 4, "i"))
c[1] = -5
assert_eq(c.tolist(), [0, -5])
grid = memoryview(bytes(range(6))).cast("B", (2, 3))
assert_eq(grid.shape, (2, 3))
assert_eq(grid.tolist(), [[0, 1, 2], [3, 4, 5]])
e = assert_raises(TypeError, memoryview(b"abc").cast, "i")
assert_eq(str(e), "memoryview: length is not a multiple of itemsize")
assert_eq(memoryview(b"\x01\x00").cast("?").tolist(), [True, False])
assert_eq(memoryview(b"ab").cast("c").tolist(), [b"a", b"b"])

# release and the context manager.
v = memoryview(b"xy")
with v as same:
    assert_is(same, v)
e = assert_raises(ValueError, len, v)
assert_eq(str(e), "operation forbidden on released memoryview object")
v.release()
assert_true(repr(v).startswith("<released memory at "))
assert_true(repr(memoryview(b"")).startswith("<memory at "))

# __buffer__ and __release_buffer__.
log = []
class Exporter:
    def __init__(self):
        self.data = bytearray(b"exported")
    def __buffer__(self, flags):
        log.append(("buffer", type(flags)))
        return memoryview(self.data)
    def __release_buffer__(self, view):
        log.append("release")
x = Exporter()
assert_eq(bytes(x), b"exported")
assert_eq(log, [("buffer", int), "release"])
log.clear()
with memoryview(x) as mv:
    assert_eq(mv.tobytes(), b"exported")
assert_eq(log, [("buffer", int), "release"])
class BadExporter:
    def __buffer__(self, flags):
        return b"not a view"
e = assert_raises(TypeError, memoryview, BadExporter())
assert_eq(str(e), "BadExporter.__buffer__() must return a memoryview, not bytes")
e = assert_raises(TypeError, memoryview, "str")
assert_eq(str(e), "memoryview: a bytes-like object is required, not 'str'")
assert_eq(b"-".join([Exporter()]), b"exported")
