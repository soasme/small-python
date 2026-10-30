# spec: PLS-315 24.2, 25.5
# description: bytearray: construction, repr, mutation, and resizing with exports.
from harness import *

b = bytearray(b"abc")
assert_eq(repr(b), "bytearray(b'abc')")
assert_eq(repr(bytearray()), "bytearray(b'')")
assert_eq(bytearray(3), bytearray(b"\0\0\0"))
assert_eq(bytearray([1, 2]), bytearray(b"\x01\x02"))
assert_eq(bytearray("é", "utf-8"), bytearray(b"\xc3\xa9"))
assert_raises(TypeError, hash, b)
assert_type(b[0], int)
assert_type(b[0:2], bytearray)
assert_eq(b[::-1], bytearray(b"cba"))
class WithBytes:
    def __bytes__(self):
        return b"xy"
assert_eq(bytes(WithBytes()), b"xy")
assert_raises(TypeError, bytearray, WithBytes())

b[0] = 65
assert_eq(b, bytearray(b"Abc"))
e = assert_raises(ValueError, b.__setitem__, 0, 256)
assert_eq(str(e), "byte must be in range(0, 256)")
e = assert_raises(TypeError, b.__setitem__, 0, "a")
assert_eq(str(e), "'str' object cannot be interpreted as an integer")
b[1:2] = b"XYZ"
assert_eq(b, bytearray(b"AXYZc"))
b[0:1] = [104, 105]
assert_eq(b, bytearray(b"hiXYZc"))
b[2:] = memoryview(b"!!")
assert_eq(b, bytearray(b"hi!!"))
e = assert_raises(TypeError, b.__setitem__, slice(0, 1), "s")
assert_eq(str(e), "can assign only bytes, buffers, or iterables of ints in range(0, 256)")
del b[0]
assert_eq(b, bytearray(b"i!!"))

b = bytearray(b"ab")
b.append(99)
b.extend(b"de")
b.extend([102])
b.insert(0, 95)
assert_eq(b, bytearray(b"_abcdef"))
assert_eq(b.pop(), 102)
assert_eq(b.pop(0), 95)
b.remove(99)
assert_eq(b, bytearray(b"abde"))
e = assert_raises(ValueError, b.remove, 120)
assert_eq(str(e), "value not found in bytearray")
c = b.copy()
c.reverse()
assert_eq((b, c), (bytearray(b"abde"), bytearray(b"edba")))
b.clear()
e = assert_raises(IndexError, b.pop)
assert_eq(str(e), "pop from empty bytearray")
assert_raises(ValueError, bytearray(b"").append, 300)
b = bytearray(b"ab")
same = b
b += b"c"
b *= 2
assert_is(b, same)
assert_eq(b, bytearray(b"abcabc"))

# b += b holds an export of b while resizing it; an empty b is not resized.
b = bytearray(b"ab")
e = assert_raises(BufferError, b.__iadd__, b)
assert_eq(str(e), "Existing exports of data: object cannot be re-sized")
assert_eq(b, bytearray(b"ab"))
b += bytearray(b"cd")
assert_eq(b, bytearray(b"abcd"))
b = bytearray()
b += b
assert_eq(b, bytearray())

# Resizing is refused while an export is held; same-length writes are allowed.
b = bytearray(b"abc")
view = memoryview(b)
e = assert_raises(BufferError, b.append, 1)
assert_eq(str(e), "Existing exports of data: object cannot be re-sized")
assert_raises(BufferError, b.extend, b"x")
assert_raises(BufferError, b.__delitem__, 0)
b[0] = 122
b[1:3] = b"yy"
assert_eq(view.tobytes(), b"zyy")
view.release()
b.append(33)
assert_eq(b, bytearray(b"zyy!"))

# A slice is a bytearray of its own that grows like any other.
for s in (bytearray(b"abcdef")[::2], bytearray(b"abcdef")[1:3]):
    t = bytes(s)
    s += b"x" * 40
    s.extend(b"yz")
    assert_eq(s, bytearray(t + b"x" * 40 + b"yz"))
