# spec: PLS-315 24.1.1, 24.2, 27.1.7
# description: bytes(x) tries __bytes__, then __index__ (falling through on TypeError), then buffers; reversed walks a bytearray.
from harness import *

class Wrapped:
    def __init__(self, value): self.value = value
    def __bytes__(self): return self.value
class Plain(bytes): pass
class Counted(bytes):
    def __index__(self): return 3
class Refusing(bytes):
    def __index__(self): raise TypeError
class Failing(bytes):
    def __index__(self): raise ValueError("no")
class Exporter:
    def __buffer__(self, flags): return memoryview(b"xy")
    def __index__(self): return 2
class Unindexable:
    def __buffer__(self, flags): return memoryview(b"xy")
    def __index__(self): raise TypeError

# bytes defines __bytes__, so its subclasses convert through it before __index__.
data = b"ab"
assert_is(data.__bytes__(), data)
assert_eq((type(Plain(b"q").__bytes__()), Plain(b"q").__bytes__()), (bytes, b"q"))
assert_eq((bytes(Counted(b"foo")), bytes(Refusing(b"foo")), bytes(Failing(b"foo"))), (b"foo", b"foo", b"foo"))
e = assert_raises(TypeError, bytes.__bytes__, 1)
assert_eq(str(e), "descriptor '__bytes__' for 'bytes' objects doesn't apply to a 'int' object")

# A __bytes__ result that is a bytes subclass is returned as it is.
result = Plain(b"abc")
assert_is(bytes(Wrapped(result)), result)
assert_eq((type(Plain(Wrapped(result))), Plain(Wrapped(result))), (Plain, b"abc"))
assert_eq(int.from_bytes(Wrapped(Plain(b"\x02"))), 2)
e = assert_raises(TypeError, bytes, Wrapped(bytearray(b"a")))
assert_eq(str(e), f"{fqname(Wrapped)}.__bytes__() must return a bytes, not bytearray")

# __index__ comes before the buffer protocol; a TypeError from it falls through.
assert_eq((bytes(Exporter()), bytes(Unindexable())), (b"\0\0", b"xy"))
assert_eq((bytearray(Exporter()), bytearray(Unindexable())), (bytearray(b"\0\0"), bytearray(b"xy")))
class Raising:
    def __index__(self): raise ValueError("no")
    def __iter__(self): return iter([1])
assert_eq(str(assert_raises(ValueError, bytes, Raising())), "no")

# bytearray skips __bytes__.
assert_eq(bytearray(Counted(b"foo")), bytearray(3))
assert_eq(str(assert_raises(TypeError, bytearray, Wrapped(b"a"))), "cannot convert 'Wrapped' object to bytearray")

# A str subclass with __bytes__ converts through it unless an encoding is given.
class Text(str):
    def __bytes__(self): return b"z"
assert_eq((bytes(Text("a")), bytes(Text("a"), "ascii")), (b"z", b"a"))
for call in (lambda: bytes(Text("a"), errors="strict"), lambda: bytes("a", errors="strict"), lambda: bytearray(Text("a"))):
    assert_eq(str(assert_raises(TypeError, call)), "string argument without an encoding")

# reversed() walks a bytearray through the sequence protocol and stops for good
# when it shrinks below the position.
array = bytearray(b"abcde")
backwards = reversed(array)
assert_eq((next(backwards), backwards.__length_hint__()), (ord("e"), 4))
del array[1:]
assert_eq((backwards.__length_hint__(), list(backwards), list(backwards)), (0, [], []))
array = bytearray(b"abc")
backwards = reversed(array)
next(backwards)
array.extend(b"xyz")
assert_eq(list(backwards), [ord("b"), ord("a")])
