# spec: PLS-315 19.3.6, 19.3.9, 7.5.3
# description: hex(), oct(), bin() and chr() of an instance with a Python
# __index__ call it once and convert the int it returns; an int's subclass
# is its int, its own __index__ not called; a non-int result raises the
# TypeError naming the class, and chr() refuses an int outside its range;
# inside functions as at module level.
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
        return 1.5

class I(int):
    def __index__(self):
        log.append("own")
        return 99

def converts():
    out = [hex(X(255)), oct(X(8)), bin(X(-3)), chr(X(65)), hex(X(1 << 70)), hex(I(3)), chr(I(66))]
    out.append(log[:])
    return out

assert_eq(converts(), ["0xff", "0o10", "-0b11", "A", "0x400000000000000000", "0x3", "B", [255, 8, -3, 65, 1 << 70]])
log.clear()
assert_eq((hex(X(7)), log), ("0x7", [7]))

def errors():
    out = []
    for convert in (hex, oct, bin, chr):
        try: convert(Real())
        except TypeError as e: out.append(str(e))
    for v in (X(-1), X(1 << 70)):
        try: chr(v)
        except (ValueError, OverflowError) as e: out.append((type(e).__name__, str(e)))
    return out

assert_eq(errors(), ["Real.__index__() must return an int, not float"] * 4 +
          [("ValueError", "chr() arg not in range(0x110000)"), ("ValueError", "chr() arg not in range(0x110000)")])
