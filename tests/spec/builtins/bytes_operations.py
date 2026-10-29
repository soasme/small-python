# spec: PLS-315 24.3, 23.3
# description: The str-like methods of bytes and bytearray: bytes-like arguments, ASCII semantics, and errors.
from harness import *

for cls in (bytes, bytearray):
    v = cls(b"Hello World")
    assert_type(v.upper(), cls)
    assert_eq(v.upper(), cls(b"HELLO WORLD"))
    assert_eq(v.split(), [cls(b"Hello"), cls(b"World")])
    assert_true(v.startswith((b"x", b"He")))
    assert_eq(v.find(b"o"), 4)
    assert_eq(v.find(111), 4)
    assert_eq(v.count(memoryview(b"l")), 3)
    assert_true(108 in v)
    assert_eq(v.replace(bytearray(b"World"), b"Bytes"), cls(b"Hello Bytes"))
assert_true(bytearray(b"a").strip() is not bytearray(b"a"))
b = bytearray(b"same")
assert_true(b.replace(b"x", b"y") is not b)

e = assert_raises(TypeError, b"abc".find, "a")
assert_eq(str(e), "argument should be integer or bytes-like object, not 'str'")
e = assert_raises(ValueError, b"abc".find, 256)
assert_eq(str(e), "byte must be in range(0, 256)")
e = assert_raises(TypeError, b"abc".split, "a")
assert_eq(str(e), "a bytes-like object is required, not 'str'")
e = assert_raises(TypeError, b"abc".startswith, "a")
assert_eq(str(e), "startswith first arg must be bytes or a tuple of bytes, not str")
e = assert_raises(TypeError, b"abc".endswith, 1)
assert_eq(str(e), "endswith first arg must be bytes or a tuple of bytes, not int")
assert_raises(TypeError, lambda: "a" in b"abc")
assert_true(memoryview(b"bc") in b"abc" and bytearray(b"c") in b"abc" and memoryview(b"bd") not in bytearray(b"abc"))
class Exporter:
    def __buffer__(self, flags): return memoryview(b"bu")
assert_true(Exporter() in b"xbuf")

# ASCII semantics.
assert_eq(b"\xe9a".upper(), b"\xe9A")
assert_false(b"\xe9".isalpha())
assert_true(b"abc1".isalnum())
assert_eq(b"a\x85b\xa0c".split(), [b"a\x85b\xa0c"])
assert_eq(b" \t\n\x0b\x0c\rx".strip(), b"x")
assert_eq(b"a\x1cb".split(), [b"a\x1cb"])
assert_eq(b"hello world".title(), b"Hello World")
assert_eq(b"hELLO".capitalize(), b"Hello")
assert_eq(b"aB".swapcase(), b"Ab")
assert_eq(b"a\nb\rc\r\nd\x0be\x1cf".splitlines(), [b"a", b"b", b"c", b"d\x0be\x1cf"])
for missing in ("casefold", "isdecimal", "isnumeric", "isidentifier", "isprintable", "format", "encode"):
    assert_false(hasattr(b"", missing), missing)

assert_eq(b"ab".center(6, b"*"), b"**ab**")
e = assert_raises(TypeError, b"ab".center, 6, "*")
assert_eq(str(e), "center() argument 2 must be a byte string of length 1, not str")
assert_raises(TypeError, b"ab".ljust, 6, b"**")
assert_eq(b"-".join([b"a", bytearray(b"b"), memoryview(b"c")]), b"a-b-c")
e = assert_raises(TypeError, b"-".join, [b"a", "b"])
assert_eq(str(e), "sequence item 1: expected a bytes-like object, str found")

table = bytes.maketrans(b"abc", b"xyz")
assert_eq(len(table), 256)
assert_eq(b"aabbcd".translate(table), b"xxyyzd")
assert_eq(b"aabbcd".translate(None, b"b"), b"aacd")
assert_eq(b"abc".translate(table, delete=b"a"), b"yz")
e = assert_raises(ValueError, b"a".translate, b"short")
assert_eq(str(e), "translation table must be 256 characters long")
e = assert_raises(ValueError, bytes.maketrans, b"ab", b"x")
assert_eq(str(e), "maketrans arguments must have same length")

assert_eq(b"\xc3\xa9".decode(), "é")
assert_eq(b"\xff".decode("utf-8", "replace"), "�")
assert_eq(bytearray(b"abc").decode("ascii"), "abc")

assert_eq(b"%s %b %r %a %c %c %d %x" % (b"x", bytearray(b"y"), "é", "é", 65, b"B", 5, 255),
          b"x y '\\xe9' '\\xe9' A B 5 ff")
class B:
    def __bytes__(self):
        return b"bytes!"
assert_eq(b"%s" % B(), b"bytes!")
e = assert_raises(TypeError, lambda: b"%b" % "s")
assert_eq(str(e), "format argument: %b requires a bytes-like object, or an object that implements __bytes__, not str")
e = assert_raises(OverflowError, lambda: b"%c" % 256)
assert_eq(str(e), "format argument: %c argument not in range(256)")
assert_type(bytearray(b"%s") % b"x", bytearray)

e = assert_raises(TypeError, lambda: b"a" + "b")
assert_eq(str(e), "can't concat str to bytes")
e = assert_raises(TypeError, lambda: bytearray(b"a") + "b")
assert_eq(str(e), "can't concat str to bytearray")
assert_type(b"a" + bytearray(b"b"), bytes)
assert_type(bytearray(b"a") + b"b", bytearray)
