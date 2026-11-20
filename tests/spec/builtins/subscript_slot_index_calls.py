# spec: PLS-315 25.5.1, 25.3.2, 7.5.3
# description: a sequence's __getitem__, __setitem__ and __delitem__ called
# as methods, bound or unbound, convert an index by its Python __index__
# once, as the subscript does, which may loop; a list's, tuple's, str's
# or bytes' index must fit the index size, naming the key's type, while
# a range's need not; a non-integer key or receiver fails before any call.
from harness import *

log = []
class I:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in (): pass
        log.append(self.v)
        return self.v

def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return [r, list(log)]

def cases():
    l = [1, 2, 3]
    ba = bytearray(b"ab")
    class L(list): pass
    big = 2 ** 100
    return [
        run(lambda: range(10)[I(3)]),
        run(lambda: range(10).__getitem__(I(4))),
        run(lambda: range(10).__getitem__(I(big))),
        run(lambda: [1, 2, 3].__getitem__(I(1))),
        run(lambda: list.__getitem__([1, 2, 3], I(-1))),
        run(lambda: [1, 2, 3].__getitem__(I(big))),
        run(lambda: "abc".__getitem__(I(1))),
        run(lambda: b"abc".__getitem__(I(1))),
        run(lambda: (1, 2).__getitem__(I(9))),
        run(lambda: L([5, 6]).__getitem__(I(1))),
        run(lambda: (l.__setitem__(I(0), 9), list(l))),
        run(lambda: (l.__delitem__(I(0)), list(l))),
        run(lambda: list.__setitem__(l, I(5), 1)),
        run(lambda: (ba.__setitem__(I(0), 65), bytes(ba))),
        run(lambda: (ba.__setitem__(I(0), 300), bytes(ba))),
        run(lambda: (ba.__delitem__(I(0)), bytes(ba))),
        run(lambda: [1].__getitem__(1.5)),
        run(lambda: (1,).__getitem__(I("x"))),
        run(lambda: list.__getitem__((1,), I(0))),
    ]

expected = [
    [3, [3]], [4, [4]], [("IndexError", "range object index out of range"), [2 ** 100]],
    [2, [1]], [3, [-1]], [("IndexError", "cannot fit 'I' into an index-sized integer"), [2 ** 100]],
    ["b", [1]], [98, [1]], [("IndexError", "tuple index out of range"), [9]], [6, [1]],
    [(None, [9, 2, 3]), [0]], [(None, [2, 3]), [0]], [("IndexError", "list assignment index out of range"), [5]],
    [(None, b"Ab"), [0]], [("ValueError", "byte must be in range(0, 256)"), [0]], [(None, b"b"), [0]],
    [("TypeError", "list indices must be integers or slices, not float"), []],
    [("TypeError", "I.__index__() must return an int, not str"), ["x"]],
    [("TypeError", "descriptor '__getitem__' for 'list' objects doesn't apply to a 'tuple' object"), []],
]
assert_eq(cases(), expected)
