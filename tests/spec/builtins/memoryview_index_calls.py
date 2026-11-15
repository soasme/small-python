# spec: PLS-315 24.4.2, 24.2, 13.3.2, 7.5.3
# description: an item of a memoryview and an item store into a
# bytearray or a writable one-dimensional memoryview, at an instance
# whose Python __index__, which may loop, gives the index, call it once
# before the item is read or written. A view that is released or has no
# dimension, and a store into a read-only or multi-dimensional view or a
# deletion from a view, fails first; a multi-dimensional item converts
# its index before it fails; a released view fails after an __index__
# releases it; an index that does not fit is an IndexError naming the
# key's class; any other exception from __index__ propagates. Inside
# functions as at module level.
from harness import *

log = []

class At:
    def __init__(self, n): self.n = n
    def __index__(self):
        for _ in (): pass
        log.append(self.n)
        if self.n == "raise": raise LookupError("at")
        return self.n

def failure(f):
    try: f()
    except Exception as e: return type(e).__name__, str(e)

def items():
    b = bytearray(b"xyz"); m = memoryview(b); k = At(1)
    out = [m[k], m[At(-1)], memoryview(b"pqr")[k], m[At(0):At(2)].tobytes()]
    b[k] = 65; m[At(2)] = 66
    out.append(bytes(b))
    return out

assert_eq(items(), [121, 122, 113, b"xy", b"xAB"])
assert_eq(log, [1, -1, 1, 0, 2, 1, 2])
log.clear()

def errors():
    grid = memoryview(bytearray(6)).cast("B", (2, 3))
    zero = memoryview(bytearray(1)).cast("B", ())
    released = memoryview(bytearray(2)); released.release()
    view = memoryview(bytearray(3))
    def store(target, key): target[key] = 1
    def delete(target, key): del target[key]
    out = [failure(lambda: grid[At("raise")]), failure(lambda: grid[At(9)]), failure(lambda: store(grid, At(0))),
           failure(lambda: zero[At(0)]), failure(lambda: store(zero, At(0))),
           failure(lambda: released[At(0)]), failure(lambda: store(released, At(0))),
           failure(lambda: store(memoryview(b"ab"), At(0))), failure(lambda: delete(view, At(0))),
           failure(lambda: view[At(10 ** 30)]), failure(lambda: store(view, At(10 ** 30))),
           failure(lambda: store(bytearray(1), At("raise"))), failure(lambda: view[At(3)])]
    class Releases:
        def __index__(self):
            for _ in (): pass
            view.release()
            return 0
    out.append(failure(lambda: view[Releases()]))
    return out

assert_eq(errors(), [("LookupError", "at"), ("NotImplementedError", "multi-dimensional sub-views are not implemented"),
                     ("NotImplementedError", "sub-views are not implemented"),
                     ("TypeError", "invalid indexing of 0-dim memory"), ("TypeError", "invalid indexing of 0-dim memory"),
                     ("ValueError", "operation forbidden on released memoryview object"),
                     ("ValueError", "operation forbidden on released memoryview object"),
                     ("TypeError", "cannot modify read-only memory"), ("TypeError", "cannot delete memory"),
                     ("IndexError", "cannot fit 'At' into an index-sized integer"),
                     ("IndexError", "cannot fit 'At' into an index-sized integer"), ("LookupError", "at"),
                     ("IndexError", "index out of bounds on dimension 1"),
                     ("ValueError", "operation forbidden on released memoryview object")])
assert_eq(log, ["raise", 9, 10 ** 30, 10 ** 30, "raise", 3])
log.clear()

view = memoryview(bytearray(b"ab")); k = At(1)
assert_eq((view[k], failure(lambda: memoryview(bytearray(4)).cast("B", (2, 2))[k])),
          (98, ("NotImplementedError", "multi-dimensional sub-views are not implemented")))
assert_eq(log, [1, 1])
