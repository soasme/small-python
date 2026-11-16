# spec: PLS-315 25.4.2, 25.4.1
# description: slice.indices(length), called or bound first, takes the
# length by its Python __index__, then the step, the start and the stop by
# theirs, which may loop, in turn: a negative length, a zero step or a part
# neither None, an int nor such an instance stops before the later parts,
# an __index__ returning no int raises TypeError, its exception
# propagates, and an int's subclass is its int, its __index__ not called;
# so does a subscript by a slice with an int subclass's part. Inside
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

class I(int):
    def __index__(self): log.append("I"); return 0

def t(f):
    try:
        r = f()
    except Exception as e:
        r = type(e).__name__ + ": " + str(e)
    out = (r, log[:])
    del log[:]
    return out

def results():
    return [t(lambda: slice(X(1), X(5), X(2)).indices(10)), t(lambda: slice(X(1), "a").indices(3)),
            t(lambda: slice("a", X(1)).indices(3)), t(lambda: slice(X(1), X(2), 0).indices(3)),
            t(lambda: slice(X(1), X(2), X(0)).indices(3)), t(lambda: slice(X(1), X(2)).indices(X(4))),
            t(lambda: slice(X(1), X(2)).indices(-1)), t(lambda: slice(X(1), X(2)).indices(X(-1))),
            t(lambda: slice(X("s"), 3).indices(5)), t(lambda: slice(X("raise"), X(3)).indices(5)),
            t(lambda: slice(I(1), X(3)).indices(5)), t(lambda: slice(None, None, X(-1)).indices(5)),
            t(lambda: slice(X(1), X(2)).indices("a")), t(lambda: (slice(X(1), X(9)).indices)(4)),
            t(lambda: [0, 1, 2, 3][I(1):X(3)]), t(lambda: "abcd"[X(1):I(3):X(1)])]

expected = [((1, 5, 2), [2, 1, 5]),
            ('TypeError: slice indices must be integers or None or have an __index__ method', [1]),
            ('TypeError: slice indices must be integers or None or have an __index__ method', []),
            ('ValueError: slice step cannot be zero', []), ('ValueError: slice step cannot be zero', [0]),
            ((1, 2, 1), [4, 1, 2]), ('ValueError: length should not be negative', []),
            ('ValueError: length should not be negative', [-1]),
            ('TypeError: X.__index__() must return an int, not str', ['s']), ('LookupError: x', ['raise']),
            ((1, 3, 1), [3]), ((4, -1, -1), [-1]), ("TypeError: 'str' object cannot be interpreted as an integer", []),
            ((1, 4, 1), [1, 9]), ([1, 2], [3]), ('bc', [1, 1])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
