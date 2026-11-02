# spec: PLS-315 7.5.4, 24.2, 24.3
# description: size and position arguments overflow with the C-type messages; bytes take __index__ bytes and buffers.
from harness import *

big = 1 << 70
SSIZE = "Python int too large to convert to C ssize_t"
INDEX = "cannot fit 'int' into an index-sized integer"
CINT = "Python int too large to convert to C int"
for call in [lambda: [].insert(big, 1), lambda: [1].pop(big), lambda: "a".center(big),
             lambda: b"a".ljust(-big), lambda: (1).to_bytes(big), lambda: bytearray(b"a").pop(big),
             lambda: "a".split(maxsplit=big), lambda: "a".replace("a", "b", big), lambda: b"ab".hex(":", big)]:
    assert_eq(str(assert_raises(OverflowError, call)), SSIZE)
def repeat_in_place():
    items = [1]
    items *= big
for call in [repeat_in_place, lambda: bytes(big), lambda: bytearray(-big), lambda: "a" * big]:
    assert_eq(str(assert_raises(OverflowError, call)), INDEX)
for call in [lambda: "\t".expandtabs(1 << 40), lambda: b"\t".expandtabs(big),
             lambda: __import__("x", None, None, None, 1 << 40)]:
    assert_eq(str(assert_raises(OverflowError, call)), CINT)
assert_eq("a\tb".expandtabs(-1), "ab")

# A single byte is an int or an __index__ object in range(0, 256).
class Index:
    def __init__(self, value): self.value = value
    def __index__(self): return self.value
assert_true(Index(98) in b"abc" and Index(98) in bytearray(b"abc") and Index(100) not in b"abc")
assert_eq(b"abc".find(Index(99)), 2)
for call in [lambda: big in b"a", lambda: Index(-1) in b"a", lambda: bytearray().append(big),
             lambda: bytearray().append(-big), lambda: b"a".count(Index(256))]:
    assert_eq(str(assert_raises(ValueError, call)), "byte must be in range(0, 256)")
assert_eq(memoryview(b"abc").index(98, -big, big), 1)
assert_raises(ValueError, memoryview(b"abc").index, 98, big)

# bytearray.extend and slice assignment name what they refuse.
class Text(str): pass
for value in ["x", Text("x")]:
    e = assert_raises(TypeError, bytearray().extend, value)
    assert_eq(str(e), "expected iterable of integers; got: 'str'")
assert_eq(str(assert_raises(TypeError, bytearray().extend, 5)), "can't extend bytearray with int")
assert_eq(str(assert_raises(TypeError, bytearray().extend, None)), "can't extend bytearray with NoneType")
def assign(value):
    b = bytearray(b"abc")
    b[0:1] = value
    return b
assert_eq(str(assert_raises(TypeError, assign, object())), "cannot convert 'object' object to bytearray")
assert_eq(assign({1: 2}), bytearray(b"\x01bc"))

# maketrans takes any bytes-like objects.
table = bytes.maketrans(memoryview(b"a"), bytearray(b"b"))
assert_eq((len(table), table[97], table[98]), (256, 98, 98))
class Exporter:
    def __buffer__(self, flags): return memoryview(b"c")
assert_eq(bytearray.maketrans(b"a", Exporter())[97], 99)
e = assert_raises(TypeError, bytes.maketrans, "a", b"b")
assert_eq(str(e), "a bytes-like object is required, not 'str'")
assert_raises(ValueError, bytes.maketrans, memoryview(b"ab"), b"b")
