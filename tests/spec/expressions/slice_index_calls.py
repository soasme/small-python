# spec: PLS-315 25.4.2, 13.3.3
# description: a subscript by a slice of a list, tuple, str, bytes,
# bytearray or range, and slice.indices(), take the step, the start and the
# stop in turn, each checked as it is reached: a part's Python __index__
# runs before a later part is refused, a zero step or a refused part stops
# before the later parts, an int's subclass is its int, and an __index__
# returning no int raises TypeError; inside functions as at module level.
from harness import *

log = []

class X:
    def __init__(self, v): self.v = v
    def __index__(self):
        for i in range(1): pass
        log.append(self.v)
        return self.v

class I(int):
    def __index__(self): log.append("I"); return 0

class Bad:
    def __index__(self):
        for i in range(1): pass
        return "s"

def name(e): return type(e).__name__ + ": " + str(e)

def subscripts():
    l = list(range(10)); out = []
    for k in (slice(X(1), X(4)), slice(X(1), None, X(2)), slice(None, X(3)), slice(2, X(5), 2), slice(X(1), "a"), slice(X(1), 3, 0),
              slice(X(1), 3, X(0)), slice(I(1), X(3)), slice(X(1), I(4)), slice(Bad(), 3), slice(X(2), Bad()), slice(X(8), X(2), X(-2))):
        try: out.append(l[k])
        except Exception as e: out.append(name(e))
        out.append(log[:]); del log[:]
    out.append(("abcdef"[X(1):X(3)], (1, 2, 3)[X(1):], range(10)[X(2):X(5)], b"xyz"[X(1):], bytearray(b"xyz")[X(2):]))
    out.append(log[:]); del log[:]
    return out

bad_index = "TypeError: slice indices must be integers or have an __index__ method"
zero = "ValueError: slice step cannot be zero"
bad_return = "TypeError: Bad.__index__() must return an int, not str"
expected = [[1, 2, 3], [1, 4], [1, 3, 5, 7, 9], [2, 1], [0, 1, 2], [3], [2, 4], [5], bad_index, [1], zero, [], zero, [0],
            [1, 2], [3], [1, 2, 3], [1], bad_return, [], bad_return, [2], [8, 6, 4], [-2, 8, 2],
            ("bc", (2, 3), range(2, 5), b"yz", bytearray(b"z")), [1, 3, 1, 2, 5, 1, 2]]
assert_eq(subscripts(), expected)

# Each container, and slice.indices() and a range, which name None too.
def orders():
    out = []
    for seq in ([1, 2, 3], (1, 2, 3), "abc", b"abc", range(3)):
        for k in (slice(X(1), "a"), slice("a", X(1)), slice(X(1), X(2), "a")):
            try: seq[k]
            except TypeError as e: log.append(str(e)[:30])
        out.append(log[:]); del log[:]
    for k in (slice(X(1), "a"), slice("a", X(1))):
        try: k.indices(3)
        except TypeError as e: log.append(str(e))
    out.append(log[:]); del log[:]
    return out

refused = "slice indices must be integers"
indices_refused = "slice indices must be integers or None or have an __index__ method"
assert_eq(orders(), [[1, refused, refused, refused]] * 5 + [[1, indices_refused, indices_refused]])
l = [0, 1, 2, 3]
assert_eq([l[X(1):X(3)], log], [[1, 2], [1, 3]])
