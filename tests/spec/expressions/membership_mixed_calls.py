# spec: PLS-315 7.8.3, 13.10
# description: x in a list or tuple, x not an instance, compares the items
# in order past items whose comparison calls no Python, a plain instance,
# a tuple or a list among them: a later item's Python __eq__, which may
# loop, is called with x, its result decides, its exception propagates,
# and an item identical to x before it matches with no call. Inside
# functions as at module level, in an if test as in an expression.
from harness import *

log = []

class Key:
    def __init__(self, n): self.n = n
    def __eq__(self, other):
        for _ in range(2): pass
        log.append((self.n, other))
        if other == "bad": raise KeyError(self.n)
        return self.n == other
    __hash__ = None

class Plain: pass

def searches():
    del log[:]
    x = 2.5
    out = [2 in [1, (1,), Plain(), Key(2)], 3 not in (Plain(), [3], Key(4), Key(3)), x in [Plain(), x, Key(9)],
           "s" in [Plain(), Key("t")]]
    if 5 in [[5], Plain(), Key(5)]: out.append("if")
    try:
        "bad" in [(), Plain(), Key(7)]
    except KeyError as e:
        out.append(e.args)
    return out + [list(log)]

expected = [True, False, True, False, "if", (7,), [(2, 2), (4, 3), (3, 3), ("t", "s"), (5, 5), (7, "bad")]]

def main():
    return searches()

assert_eq(main(), expected)
assert_eq(searches(), expected)
