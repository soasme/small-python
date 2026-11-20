# spec: PLS-315 24.3
# description: bytes find, rfind, index, rindex and count, given a needle
# whose class defines a Python __index__ that may loop and no
# __buffer__, call it once, after the bounds' __index__, and search for
# the byte of its int, bound or unbound; an int out of range(0, 256)
# raises ValueError and a non-int result TypeError, an exception of
# __index__ propagates, and startswith() takes no such needle. Inside
# functions as at module level.
from harness import *

log = []

class X:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in range(2): pass
        log.append(self.v)
        if self.v == "raise": raise LookupError("x")
        return self.v

def t(call):
    try:
        r = call()
    except Exception as e:
        r = type(e).__name__ + ": " + str(e)
    out = (r, log[:])
    del log[:]
    return out

def results():
    b = b"abcb"
    return [t(lambda: b.find(X(98))), t(lambda: b.rfind(X(98))), t(lambda: b.index(X(99))), t(lambda: b.rindex(X(98), 0, 3)),
            t(lambda: b.count(X(98))), t(lambda: b.find(X(300))), t(lambda: b.find(X("s"))), t(lambda: b.find(X("raise"))),
            t(lambda: b.index(X(120))), t(lambda: b.find(X(98), X(2))), t(lambda: bytes.find(b, X(98))),
            t(lambda: b.startswith(X(97)))]

expected = [(1, [98]), (3, [98]), (2, [99]), (1, [98]), (2, [98]), ("ValueError: byte must be in range(0, 256)", [300]),
            ("TypeError: X.__index__() must return an int, not str", ["s"]), ("LookupError: x", ["raise"]),
            ("ValueError: subsection not found", [120]), (3, [2, 98]), (1, [98]),
            ("TypeError: startswith first arg must be bytes or a tuple of bytes, not X", [])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)

# With instance bounds, the bounds convert first, then the needle, bound,
# through the class, or of a bytearray.
def bounded():
    b = b"abcb"
    return [t(lambda: bytes.find(b, X(98), X(2))), t(lambda: b.count(X(98), X(0), X(4))),
            t(lambda: bytearray(b).rfind(X(98), 0, X(3))), t(lambda: bytearray.index(bytearray(b), X(99), X(1))),
            t(lambda: b.find(X(300), X(1))), t(lambda: b.find(X("raise"), X(1))), t(lambda: b.find(X(98), X("raise"))),
            t(lambda: b.find(X(98), None, X(3)))]
expected_bounded = [(3, [2, 98]), (2, [0, 4, 98]), (1, [3, 98]), (2, [1, 99]),
                    ("ValueError: byte must be in range(0, 256)", [1, 300]), ("LookupError: x", [1, "raise"]),
                    ("LookupError: x", ["raise"]), (1, [3, 98])]
assert_eq(bounded(), expected_bounded)
assert_eq((lambda: bounded())(), expected_bounded)
