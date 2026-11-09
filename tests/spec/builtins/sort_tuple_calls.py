# spec: PLS-315 25.1.4, 19.3.34, 25.5.3
# description: Sorting tuples compares them as tuple comparison does: the
# first pair of items that are not one and not equal by __eq__ decides by
# __lt__, else the shorter tuple orders first. A Python __eq__ or __lt__
# of the items is called with them, an item compared with itself is not,
# a NotImplemented falls back to the reflected method and then identity,
# and an exception from either propagates out of the sort, with or
# without a key and reversed, inside functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class P:
    def __init__(self, v): self.v = v
    def __eq__(self, other):
        spin()
        log.append("eq")
        return self.v == other.v
    def __lt__(self, other):
        spin()
        log.append("lt")
        if self.v == 9: raise KeyError(9)
        return self.v < other.v
    def __repr__(self): return "P(%d)" % self.v

class Lazy:
    def __init__(self, v): self.v = v
    def __eq__(self, other):
        log.append("lazy")
        return NotImplemented
    def __lt__(self, other): return self.v < other.v

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def values(pairs):
    return [(a, b.v) for a, b in pairs]

def results():
    del log[:]
    p = [P(i) for i in range(4)]
    out = [values(sorted([(1, p[3]), (0, p[2]), (1, p[1]), (0, p[0])])),
           values(sorted([(1, p[3]), (1, p[1]), (1, p[1])], reverse=True)),
           [len(t) for t in sorted([(p[1], 2), (p[1],), (P(1), 1)])],
           sorted([3, 1, 2], key=lambda i: (i % 2, p[i])),
           error(lambda: sorted([(0, P(1)), (0, P(9))])),
           error(lambda: sorted([(0, p[1]), (0, 1)])), error(lambda: sorted([p[1], 5]))]
    ys = [(0, P(2)), (0, P(1))]
    ys.sort()
    lazy = sorted([(Lazy(2), 0), (Lazy(1), 1)])
    out += [values(ys), [t[1] for t in lazy], "eq" in log, "lt" in log, "lazy" in log]
    return out

expected = [[(0, 0), (0, 2), (1, 1), (1, 3)], [(1, 3), (1, 1), (1, 1)], [1, 2, 2], [2, 1, 3],
            ("KeyError", "9"), ("AttributeError", "'int' object has no attribute 'v'"),
            ("TypeError", "'<' not supported between instances of 'int' and 'P'"), [(0, 1), (0, 2)], [1, 0],
            True, True, True]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
