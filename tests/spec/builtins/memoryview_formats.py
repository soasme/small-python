# spec: PLS-315 24.4
# description: Items read and written through every native memoryview format, and zero-dimensional views.
from harness import *

def view(f, n=16):
    return memoryview(bytearray(n)).cast(f)
def bad(error, kind, m, v):
    def store(): m[0] = v
    assert_raises(error, store, message=f"memoryview: invalid {kind} for format '{m.format}'")

for f in "bhilqn":
    m = view(f)
    m[0] = -1; assert_eq(m[0], -1)
    bad(ValueError, "value", m, 2**70)
    bad(TypeError, "type", m, 1.5)
for f in "BHILQN":
    m = view(f)
    m[0] = 7; assert_eq(m[0], 7)
    bad(ValueError, "value", m, -1)
    bad(TypeError, "type", m, None)
m = view("P")
m[0] = -1; assert_eq(m[0], 2**(8 * m.itemsize) - 1)
m[0] = 2**(8 * m.itemsize) - 1; assert_eq(m[0], 2**(8 * m.itemsize) - 1)
bad(ValueError, "value", m, 2**(8 * m.itemsize))
bad(ValueError, "value", m, -2**(8 * m.itemsize - 1) - 1)

class F:
    def __float__(self): return 2.5
class I:
    def __index__(self): return 3
class C:
    def __complex__(self): return 1j
for f in "fde":
    m = view(f)
    m[0] = F(); assert_eq(m[0], 2.5)
    m[0] = I(); assert_eq(m[0], 3.0)
    for v in ("1", b"1", 1j, C()):
        bad(TypeError, "type", m, v)
    bad(ValueError, "value", m, 2**2000)

m = view("?")
m[0] = [1]; assert_eq(m[0], True)
m[0] = ""; assert_eq(m[0], False)
m = view("c")
m[0] = b"a"; assert_eq(m[0], b"a")
bad(ValueError, "value", m, b"ab")
bad(TypeError, "type", m, True)

m = view("d", 8)
assert_eq((m.count(0.0), m.index(0.0)), (1, 0))
assert_eq(memoryview(b"abcb").index(98, -2), 3)
assert_eq(memoryview(b"abcb").index(98, 0, 2), 1)
assert_raises(ValueError, memoryview(b"ab").index, 98, 0, 1, message="memoryview.index(x): x not found")
assert_eq(hash(memoryview(b"ab")), hash(b"ab"))

z = view("Q", 8).cast("B").cast("Q", shape=[])
assert_eq((z.ndim, z[()]), (0, 0))
assert_true(z[...] is z)
z[()] = 5; assert_eq(z.tolist(), 5)
z[...] = 6; assert_eq(z.tolist(), 6)
for k in (0, "a"):
    assert_raises(TypeError, lambda: z[k], message="invalid indexing of 0-dim memory")
def store0(): z[0] = 1
assert_raises(TypeError, store0, message="invalid indexing of 0-dim memory")
def store_key(): memoryview(bytearray(b"ab"))["x"] = 1
assert_raises(TypeError, store_key, message="memoryview: invalid slice key")
assert_eq((memoryview(b"a") == 1, memoryview(b"a").__eq__(object())), (False, NotImplemented))
