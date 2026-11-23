# spec: PLS-315 13.3.3, 25.4.2
# description: a store to, or a deletion of, a list's slice whose parts
# have a Python __index__, which may loop, calls the step's, the start's,
# then the stop's once each, before it takes the assigned items; also for
# a list subclass and an augmented slice store, which loads with them
# first. An __index__ that raises or returns no int stops it, the list
# as it was, and an extended slice still needs as many items.
from harness import *

log = []

class I:
    def __init__(self, n): self.n = n
    def __index__(self):
        for _ in (): pass
        log.append(self.n)
        if self.n == 99: raise KeyError("i")
        if self.n == 98: return "x"
        return self.n

def items():
    for x in "ab":
        log.append(x)
        yield x

def stores():
    a = list(range(8))
    a[I(1):I(3)] = items()
    out = [list(a)]
    del a[I(5):]
    out.append(list(a))
    a[I(0):I(6):I(2)] = [7, 8, 9]
    out.append(list(a))
    del a[::I(2)]
    out.append(list(a))
    class L(list): pass
    l = L([1, 2, 3]); l[I(0):1] = [5]; del l[I(2):]
    out.append(list(l))
    for bad in (99, 98):
        try: a[I(1):I(bad)] = [1]
        except (KeyError, TypeError) as e: out.append((type(e).__name__, str(e)))
    try: a[I(0):I(2):I(1)] = 5
    except TypeError as e: out.append(str(e))
    try: a[I(0):I(1):I(2)] = [1, 2]
    except ValueError as e: out.append(str(e))
    b = [0, 1, 2]; b[1:I(2)] += [5]
    out += [a, b]
    return out

expected = [[0, "a", "b", 3, 4, 5, 6, 7], [0, "a", "b", 3, 4], [7, "a", 8, 3, 9], ["a", 3], [5, 2], ("KeyError", "'i'"),
            ("TypeError", "I.__index__() must return an int, not str"), "must assign iterable to extended slice",
            "attempt to assign sequence of size 2 to extended slice of size 1", ["a", 3], [0, 1, 5, 2]]
assert_eq(stores(), expected)
assert_eq(log, [1, 3, "a", "b", 5, 2, 0, 6, 2, 0, 2, 1, 99, 1, 98, 1, 0, 2, 2, 0, 1, 2, 2])
log.clear()

a = [0, 1, 2, 3]
a[I(1):I(2)] = [9, 9]
del a[I(0):I(1)]
assert_eq((a, log), ([9, 9, 2, 3], [1, 2, 0, 1]))

# A bytearray's slice store converts the parts the same way, then copies a
# bytes value; a zero step refuses an iterated value before taking it.
class ByteAt:
    def __init__(self, n): self.n = n
    def __index__(self): return self.n
stored_bytes = bytearray(b"abc")
stored_bytes[ByteAt(0):ByteAt(1)] = b"xy"
assert_eq(stored_bytes, bytearray(b"xybc"))
with assert_raises(ValueError, message="slice step cannot be zero"):
    stored_bytes[0:2:ByteAt(0)] = (x for x in b"ab")
assert_eq(stored_bytes, bytearray(b"xybc"))
