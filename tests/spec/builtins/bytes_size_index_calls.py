# spec: PLS-315 24.1.1, 24.2, 7.5.4
# description: bytes() and bytearray() of an instance with a Python
# __index__, and no __bytes__ for bytes(), call it once and make that many
# zero bytes; a negative count raises ValueError, a count outside the
# index-size range OverflowError naming the instance's type, and a
# TypeError from __index__ leaves the iterable form; bytes() calls a
# __bytes__ instead; inside functions as at module level.
from harness import *

log = []

class X:
    def __init__(self, i): self.i = i
    def __index__(self):
        for _ in (): pass
        log.append(self.i)
        return self.i

class Real:
    def __index__(self):
        for _ in (): pass
        log.append("real")
        return 1.5

class Both(X):
    def __bytes__(self):
        for _ in (): pass
        return b"own"

def sizes():
    out = [bytes(X(2)), bytearray(X(3)), bytes(Both(5)), bytearray(Both(1))]
    out.append(log[:])
    return out

assert_eq(sizes(), [b"\0\0", bytearray(b"\0\0\0"), b"own", bytearray(b"\0"), [2, 3, 1]])
log.clear()
assert_eq((bytes(X(1)), log), (b"\0", [1]))

def errors():
    out = []
    for make in (bytes, bytearray):
        for v in (X(-1), X(1 << 70), Real()):
            log.clear()
            try: make(v)
            except (ValueError, OverflowError, TypeError) as e: out.append((type(e).__name__, str(e), log[:]))
    return out

assert_eq(errors(), [
    ("ValueError", "negative count", [-1]),
    ("OverflowError", "cannot fit 'X' into an index-sized integer", [1 << 70]),
    ("TypeError", "cannot convert 'Real' object to bytes", ["real"]),
    ("ValueError", "negative count", [-1]),
    ("OverflowError", "cannot fit 'X' into an index-sized integer", [1 << 70]),
    ("TypeError", "cannot convert 'Real' object to bytearray", ["real"]),
])
