# spec: PLS-315 24.2, 24.3
# description: bytearray methods whose arguments run Python code that resizes the array.
from harness import *

RESIZE = "Existing exports of data: object cannot be re-sized"

class Clearing:
    """A byte or buffer argument whose conversion clears the array."""
    def __init__(self, array, data=b"A"):
        self.array = array
        self.data = data
    def __index__(self):
        self.array.clear()
        return ord("A")
    def __buffer__(self, flags):
        self.array.clear()
        return memoryview(self.data)

# Methods holding an export refuse the resize.
for call in (lambda b, e: b.find(e), lambda b, e: b.count(e), lambda b, e: b.split(e),
             lambda b, e: b.rsplit(e), lambda b, e: b.hex(e), lambda b, e: e in b,
             lambda b, e: b.join([e])):
    b = bytearray(b"A")
    assert_raises((BufferError, TypeError), call, b, Clearing(b))
    assert_eq(b, bytearray(b"A"))
b = bytearray(b"%s")
assert_eq(str(assert_raises(BufferError, lambda: b % Clearing(b))), RESIZE)
b = bytearray(b"A")
assert_eq(str(assert_raises(TypeError, b.join, [Clearing(b)])), "sequence item 0: expected a bytes-like object, Clearing found")

# These convert their arguments before reading the receiver.
b = bytearray(b"A")
assert_eq(b.replace(Clearing(b, b""), b"x"), bytearray(b"x"))
b = bytearray(b"A")
assert_eq(b.removeprefix(Clearing(b)), bytearray())
b = bytearray(b"A")
assert_eq(b.strip(Clearing(b)), bytearray())

# __init__ empties the array, and refuses while an export is held.
b = bytearray(b"abc")
b.__init__(b"x")
assert_eq(b, bytearray(b"x"))
view = memoryview(b)
assert_eq(str(assert_raises(BufferError, b.__init__, b"yz")), RESIZE)
view.release()

# join takes the items first and rechecks the length after each buffer.
log = []
class Logged:
    def __init__(self, n): self.n = n
    def __buffer__(self, flags):
        log.append(("buffer", self.n))
        return memoryview(b"x")
def items():
    for n in range(2):
        log.append(("item", n))
        yield Logged(n)
assert_eq(b"-".join(items()), b"x-x")
assert_eq(log, [("item", 0), ("item", 1), ("buffer", 0), ("buffer", 1)])
class Mutating:
    def __init__(self, mutate): self.mutate = mutate
    def __buffer__(self, flags):
        self.mutate(seq)
        return memoryview(b"x")
for sep in (b"", bytearray(b"::")):
    seq = [b"a", Mutating(lambda s: s.clear()), b"c"]
    assert_eq(str(assert_raises(RuntimeError, sep.join, seq)), "sequence changed size during iteration")
    def replace(s): s[1] = b"z"
    seq = [b"a", Mutating(replace), b"c"]
    assert_eq(sep.join(seq), sep.join([b"a", b"x", b"c"]))
assert_eq(str(assert_raises(TypeError, b"".join, 5)), "can only join an iterable")

# extend places a buffer at the length before its conversion.
class Resizing:
    def __init__(self, resize): self.resize = resize
    def __buffer__(self, flags):
        self.resize()
        return memoryview(b"AB")
b = bytearray(b"x" * 4)
b.extend(Resizing(b.clear))
assert_eq(b, bytearray(b"AB"))
b = bytearray(b"x" * 4)
b.extend(Resizing(lambda: b.extend(b"yy")))
assert_eq(b, bytearray(b"xxxxAByy"))
b = bytearray(b"ab")
def grow():
    yield 1
    b.extend(b"zz")
    yield 2
b.extend(grow())
assert_eq(b, bytearray(b"abzz\x01\x02"))
