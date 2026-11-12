# spec: PLS-315 24.4.2
# description: A memoryview released by a conversion it runs, the exports that make release() fail, the kept hash, and '?' items of any nonzero byte.
from harness import *

def forbidden(thunk):
    e = assert_raises(ValueError, thunk)
    assert_eq(str(e), "operation forbidden on released memoryview object")

# An index or an item converted by __index__, __float__ or __bool__ that
# releases the view: nothing is read or written.
data = bytearray(b"\xff" * 16)
class Releasing:
    def __init__(self, result):
        self.result = result
    def __index__(self):
        m.release()
        data[:] = b""
        return self.result
    __float__ = __bool__ = __index__

def setitem(key, value):
    m[key] = value

for fmt, value in (("B", Releasing(4)), ("i", Releasing(4)), ("d", Releasing(4.5)), ("?", Releasing(True))):
    data[:] = b"\xff" * 16
    m = memoryview(data).cast(fmt)
    forbidden(lambda: setitem(0, value))
    assert_eq(data, bytearray())
for key in (lambda: Releasing(1), lambda: (Releasing(1), 0)):
    data[:] = b"\xff" * 16
    m = memoryview(data).cast("B", (8, 2)) if isinstance(key(), tuple) else memoryview(data)
    forbidden(lambda: m[key()])
    data[:] = b"\xff" * 16
    m = memoryview(data).cast("B", (8, 2)) if isinstance(key(), tuple) else memoryview(data)
    forbidden(lambda: setitem(key(), 1))
data[:] = b"\xff" * 16
m = memoryview(data)
forbidden(lambda: setitem(slice(Releasing(2)), b"ab"))
assert_eq(data, bytearray())
# Reading a slice of a view released meanwhile still gives the slice.
data = bytearray(b"abcdef")
m = memoryview(data)
class Stop:
    def __index__(self):
        m.release()
        return 2
assert_eq(bytes(m[:Stop()]), b"ab")

# hash(m) exports m while it hashes the exporter; m.hex(sep) while it
# converts sep, for a C-contiguous view only.
class Exporter(bytearray):
    def __hash__(self):
        m.release()
        return 1
m = memoryview(Exporter(b"ab")).toreadonly()
e = assert_raises(BufferError, hash, m)
assert_eq(str(e), "memoryview has 1 exported buffer")
assert_eq(bytes(m), b"ab")
class Sep(bytes):
    def __len__(self):
        m.release()
        return 1
m = memoryview(bytearray(b"ab"))
e = assert_raises(BufferError, m.hex, Sep(b":"))
assert_eq(str(e), "memoryview has 1 exported buffer")
m = memoryview(bytearray(b"abcd"))[::2]
assert_eq(m.hex(Sep(b":")), "61:63")
forbidden(lambda: m.tobytes())

# The hash is kept once computed, through release.
m = memoryview(b"abc")
h = hash(m)
m.release()
assert_eq(hash(m), h)
assert_eq(m.__hash__(), h)
m = memoryview(b"abc")
m.release()
forbidden(lambda: hash(m))

# A '?' item is true when any byte of it is nonzero.
assert_eq(memoryview(b"\0\2\0\x80").cast("?").tolist(), [False, True, False, True])
assert_eq(memoryview(b"\1\3").cast("?"), memoryview(b"\2\4").cast("?"))
