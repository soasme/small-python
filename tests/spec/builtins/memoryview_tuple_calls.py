# spec: PLS-315 24.4.2, 7.5.3
# description: an item of a multi-dimensional memoryview, read, stored or
# updated in place, at a tuple of ints and instances calls each instance's
# Python __index__, which may loop, in order, checking each dimension's
# index before the next item's call: one out of bounds is an IndexError
# naming its dimension, an int too big for an index one naming the
# instance's class; a non-int from __index__ and its exceptions
# propagate. A tuple shorter than the dimensions, a read-only view and a
# deletion fail before any call. Inside functions as at module level.
from harness import *

log = []

class I:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in (): pass
        log.append(self.v)
        if self.v == "big": return 1 << 70
        if self.v == "str": return "s"
        if self.v == "raise": raise LookupError("i")
        return self.v

def failure(f):
    try: f()
    except Exception as e: return type(e).__name__ + ": " + str(e)

def run():
    for _ in (): pass
    m = memoryview(bytearray(range(24))).cast("B", (2, 3, 4))
    out = [m[I(1), I(2), I(3)], m[0, I(1), 2], m[I(-1), 0, I(-1)]]
    m[I(1), 0, I(0)] = 77
    m[1, I(1), 1] += 10
    out.append((m[1, 0, 0], m[1, 1, 1]))
    out.append(failure(lambda: m[I(5), I(0), 0]))
    def store(): m[0, 9, I(0)] = 1
    out.append(failure(store))
    def big(): m[I(0), I("big"), 0] = 1
    out.append(failure(big))
    out.append(failure(lambda: m[I("str"), 0, 0]))
    out.append(failure(lambda: m[I("raise"), 0, 0]))
    out.append(failure(lambda: m[I(0), I(0)]))
    def gone(): del m[I(0), I(0), I(0)]
    out.append(failure(gone))
    r = memoryview(bytes(6)).cast("B", (2, 3))
    def read_only(): r[I(0), I(0)] = 1
    out.append(failure(read_only))
    return out

expected = [23, 6, 15, (77, 27), "IndexError: index out of bounds on dimension 1", "IndexError: index out of bounds on dimension 2",
            "IndexError: cannot fit 'I' into an index-sized integer", "TypeError: I.__index__() must return an int, not str",
            "LookupError: i", "NotImplementedError: sub-views are not implemented", "TypeError: cannot delete memory",
            "TypeError: cannot modify read-only memory"]
expected_log = [1, 2, 3, 1, -1, -1, 1, 0, 1, 1, 5, 0, "big", "str", "raise"]
assert_eq(run(), expected)
assert_eq(log, expected_log)
log.clear()

m = memoryview(bytearray(range(6))).cast("B", (2, 3))
m[I(1), I(2)] = 50
assert_eq((m[I(1), I(2)], m.tolist(), log), (50, [[0, 1, 2], [3, 4, 50]], [1, 2, 1, 2]))
