# spec: PLS-315 7.2.4, 19.3.34, 25.1.4
# description: sorting tuples whose items pair a builtin value with an
# instance compares those items by the instance's reflected Python
# __eq__ and then its __lt__ or reflected __gt__, as RichCompare does
# when the builtin's method returns NotImplemented; each comparison's
# result decides, an exception from one propagates out of the sort, and
# lists sort alike, with a key and reversed, inside functions as at
# module level.
from harness import *

seen = set()

def spin():
    for _ in range(2): pass

class R:
    def __init__(self, v): self.v = v
    def __eq__(self, other):
        spin()
        seen.add(("eq", self.v, other))
        return self.v == other if type(other) is int else NotImplemented
    def __lt__(self, other):
        return self.order(other, self.v < other)
    def __gt__(self, other):
        return self.order(other, self.v > other)
    def order(self, other, result):
        # Which pairs a sort compares, and in which direction, is the
        # implementation's choice (25.1.4): both directions log alike.
        spin()
        seen.add(("order", self.v, other))
        if other == 9: raise KeyError(9)
        return result
    __hash__ = None

def plain(t):
    return [x if type(x) is int else ("R", x.v) for x in t]

def results():
    seen.clear()
    out = [[plain(t) for t in sorted([(0, R(1)), (0, 2), (0, 0)])],
           [plain(t) for t in sorted([(0, R(1)), (0, 2), (0, 0)], reverse=True)],
           sorted([2, 0], key=lambda i: (1, R(1) if i else i)),
           plain(sorted([2, R(1), 0])),
           [plain(t) for t in sorted([[1, R(2)], [1, 1]])]]
    calls = sorted({name for name, _, _ in seen})
    seen.clear()
    try:
        sorted([(0, R(1)), (0, 9)])
    except KeyError as e:
        out.append(("KeyError", e.args))
    return out, calls, sorted(seen)

expected = ([[[0, 0], [0, ("R", 1)], [0, 2]], [[0, 2], [0, ("R", 1)], [0, 0]], [0, 2],
             [0, ("R", 1), 2], [[1, 1], [1, ("R", 2)]], ("KeyError", (9,))],
            ["eq", "order"],
            [("eq", 1, 9), ("order", 1, 9)])

assert_eq(results(), expected)
def main():
    return results()
assert_eq(main(), expected)
