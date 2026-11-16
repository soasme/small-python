# spec: PLS-315 24.3
# description: in and not in of bytes, given an object whose class
# defines a Python __index__ that may loop, call it once and search for
# the byte of its int, in a display and a conditional too; an int out of
# range(0, 256) raises ValueError, and when __index__ raises or returns
# a non-int its exception is discarded and the operand is taken as a
# bytes-like needle, raising TypeError. Inside functions as at module
# level.
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
    b = b"abc"
    return [t(lambda: X(97) in b), t(lambda: X(1) in b), t(lambda: X(97) not in b), t(lambda: X(300) in b),
            t(lambda: X(-1) in b), t(lambda: X(1 << 70) in b), t(lambda: X("s") in b), t(lambda: X("raise") in b),
            t(lambda: [X(99) in b, 1]), t(lambda: 1 if X(98) in b else 0), t(lambda: X(97) in b in [True])]

expected = [(True, [97]), (False, [1]), (False, [97]), ('ValueError: byte must be in range(0, 256)', [300]),
            ('ValueError: byte must be in range(0, 256)', [-1]),
            ('ValueError: byte must be in range(0, 256)', [1180591620717411303424]),
            ("TypeError: a bytes-like object is required, not 'X'", ['s']),
            ("TypeError: a bytes-like object is required, not 'X'", ['raise']), ([True, 1], [99]), (1, [98]),
            (False, [97])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
