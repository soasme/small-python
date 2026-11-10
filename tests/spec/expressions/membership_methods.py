# spec: PLS-315 7.8.3, 13.10
# description: x in a list, a tuple or an iterator over one compares each
# item v with x as v == x, in order, inside functions as at module level:
# v's __eq__, which may loop, or x's reflected one first for a builtin v;
# the first true result stops the search, an identical item matches with
# no call, NotImplemented falls back to the other operand, a list shrunk
# by a comparison ends the search, and an iterator is consumed up to the
# match. A builtin x, or a class, calls the items' reflected __eq__ alike,
# and an if or while test of in or not in searches as an expression does.
from harness import *

log = []

class Key:
    def __init__(self, n): self.n = n
    def __eq__(self, other):
        for _ in range(2): pass
        log.append((self.n, other if isinstance(other, int) else getattr(other, "n", type(other).__name__)))
        return isinstance(other, Key) and self.n == other.n
    __hash__ = None

class Decline:
    def __eq__(self, other): return NotImplemented

class Truthy:
    def __init__(self, truth): self.truth = truth
    def __bool__(self): return self.truth

class Odd:
    def __init__(self, truth): self.truth = truth
    def __eq__(self, other): return Truthy(self.truth)

class Raising:
    def __eq__(self, other): raise KeyError("eq")

class Plain:
    pass

class Narrow:
    def __eq__(self): return True

class Shrinking:
    def __init__(self, into): self.into = into
    def __eq__(self, other):
        self.into.clear()
        return False

def searches():
    del log[:]
    k1, k2 = Key(1), Key(2)
    out = [k2 in [k1, k2, Key(3)], list(log)]
    del log[:]
    out += [k2 in (1, k1), list(log)]
    del log[:]
    out += [k1 in [k1], k1 not in [Key(5), k1], list(log)]
    d = Decline()
    out += [d in [Decline()], d in [d], Key(4) in [Decline()]]
    out += [Odd(True) in [Odd(False)], Odd(False) in [Odd(True)]]
    target = []
    target += [Shrinking(target), Key(9)]
    out.append(Key(9) in target)
    del log[:]
    it = iter([Key(7), Key(8), Key(9)])
    out += [Key(8) in it, [k.n for k in it]]
    # Items no Python compares come first, natively.
    plain = Plain()
    del log[:]
    out += [plain in [1, "a", Key(6), plain], list(log)]
    del log[:]
    keys = [Key(1), Key(2), 3, Key(4)]
    out += [3 in keys, 4 in keys, 5 not in (Key(5),), 2 in [1, Plain(), Key(2)], list(log)]
    del log[:]
    tests = []
    if Key(2) in keys: tests.append("in")
    if Key(9) not in keys: tests.append("not in")
    if 3 in keys: tests.append("native")
    if 7 in keys: tests.append("never")
    n = 0
    while Key(n) not in keys: n += 1
    out += [tests, n, list(log)]
    del log[:]
    out += [int in [str, Key(1), int], str not in (Key(2),), list(log)]
    try:
        Narrow() in [Narrow()]
    except TypeError as e:
        out.append(str(e))
    try:
        Key(1) in [Raising(), Key(1)]
    except KeyError as e:
        out.append(e.args)
    return out

expected = [True, [(1, 2)], False, [(2, 1), (1, 2)], True, False, [(5, 1)],
            False, True, False, False, True, False, True, [9], True, [(6, "Plain")],
            True, False, True, False, [(1, 3), (2, 3), (1, 4), (2, 4), (4, 4), (5, 5), (2, 2)],
            ["in", "not in", "native"], 1,
            [(1, 2), (2, 2), (1, 9), (2, 9), (9, 3), (4, 9), (1, 3), (2, 3), (1, 7), (2, 7), (4, 7),
             (1, 0), (2, 0), (0, 3), (4, 0), (1, 1)],
            True, True, [(1, "type"), (2, "type")],
            "Narrow.__eq__() takes 1 positional argument but 2 were given", ("eq",)]
assert_eq(searches(), expected)
assert_eq(Key(8) in [Key(7), Key(8)], True)
