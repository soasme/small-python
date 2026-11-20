# spec: PLS-315 7.5.4, 24.2, 24.4.2
# description: A slice store into, or deletion from, a bytearray, and a
# slice store into a writable one-dimensional memoryview, converts the
# slice's start, stop and step by their Python __index__, the step first,
# then the start and the stop, before the store; a bytearray given a
# value that is no other bytearray stores a copy of it, converting the
# slice again; an __index__ that
# resizes the bytearray is seen by the store, an error of __index__
# propagates and leaves the bytearray as it was, and a result that is no
# int raises TypeError.
from harness import *

log = []
class I:
    def __init__(self, v, array=None): self.v = v; self.array = array
    def __index__(self):
        for _ in (): pass
        log.append(self.v)
        if self.v == "bad": raise KeyError("bad")
        if self.array is not None: self.array.extend(b"Z")
        return self.v

def attempt(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))

def results():
    for _ in (): pass
    del log[:]
    a = bytearray(b"abcdef")
    a[I(1):I(3)] = b"XY"
    b = bytearray(b"abcdef")
    del b[I(0)::I(2)]
    r = bytearray(b"abc")
    r[I(0, r):] = b"Q"
    e = bytearray(b"abc")
    err = [attempt(lambda: e.__setitem__(slice(I("bad"), None), b"x")), attempt(lambda: e.__setitem__(slice(I("x")), b"x")), e]
    m = bytearray(b"abcd")
    v = memoryview(m)
    v[I(1):I(3)] = b"XY"
    s = bytearray(b"abc")
    s[I(0):I(1)] = bytearray(b"MN")
    return [a, b, r, err, m, s], list(log)

expected = ([bytearray(b"aXYdef"), bytearray(b"bdf"), bytearray(b"Q"),
             [("KeyError", "'bad'"), ("TypeError", "I.__index__() must return an int, not str"), bytearray(b"abc")],
             bytearray(b"aXYd"), bytearray(b"MNbc")],
            [1, 3, 1, 3, 2, 0, 0, 0, "bad", "x", 1, 3, 0, 1])

assert_eq(results(), expected)
assert_eq(results(), expected)
