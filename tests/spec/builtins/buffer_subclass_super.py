# spec: PLS-315 24.4.1
# description: a bytes or bytearray subclass's __buffer__ may return
# super().__buffer__(flags), a view of its own contents, which goes back
# with the copy, so the array can be resized after; one returning another
# object's view reads that view, and bytearray's own __release_buffer__ is
# not called for it. bytes(), bytearray(), memoryview(), int.from_bytes
# and map(bytes, ...) take either, while a bytes %b of a bytearray's
# subclass reads its contents; inside functions as at module level.
from harness import *

log = []
class Z(bytearray):
    def __buffer__(self, flags):
        log.append("get")
        return super().__buffer__(flags)
class B(bytes):
    def __buffer__(self, flags):
        log.append("get")
        return super().__buffer__(flags)
class W(bytearray):
    def __buffer__(self, flags):
        log.append("get")
        return memoryview(b"w")

def taken(f):
    r = f()
    got = list(log); log.clear()
    return r, got

z = Z(b"ab")
assert_eq(taken(lambda: (bytes(z), bytearray(z), int.from_bytes(z), list(map(bytes, [z])), b"%b" % (z,))),
          ((b"ab", bytearray(b"ab"), 24930, [b"ab"], b"ab"), ["get"] * 4))
z.append(99)
assert_eq(z, Z(b"abc"))
with memoryview(z) as m:
    assert_eq(m.tobytes(), b"abc")
z.append(100)
assert_eq(z, Z(b"abcd"))
log.clear()
# bytes() of a bytes subclass takes its __bytes__.
assert_eq(taken(lambda: (bytes(B(b"q")), int.from_bytes(B(b"\x01")))), ((b"q", 1), ["get"]))
w = W(b"q")
assert_eq(taken(lambda: (bytes(w), int.from_bytes(w), list(map(bytes, [w])), b"%b" % (w,))), ((b"w", 119, [b"w"], b"q"), ["get"] * 3))
w.append(1)
log.clear()
assert_eq(len(w), 2)
def inside():
    y = Z(b"xy")
    data = bytes(y)
    y.extend(b"z")
    return data, y
assert_eq(taken(inside), ((b"xy", Z(b"xyz")), ["get"]))
