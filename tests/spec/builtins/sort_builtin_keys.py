# spec: PLS-315 19.3.26, 19.3.34, 25.1.4
# description: sorted(), list.sort(), min() and max() with a builtin key
# function, len, repr, str, abs or hash, call each item's Python
# __len__, __repr__, __str__, __abs__ or __hash__ once, in item order and
# before any comparison, each of which may loop, then order by the keys;
# a key's error propagates, leaving a list.sort's list as it was, and the
# items that are not instances take their keys in C. Positional items
# and an iterable, inside functions as at module level.
from harness import *

log = []

class Item:
    def __init__(self, n): self.n = n
    def __len__(self):
        for _ in (): pass
        log.append(("len", self.n))
        if self.n < 0: raise LookupError("len")
        return self.n
    def __repr__(self):
        for _ in (): pass
        log.append(("repr", self.n))
        return "i" + str(self.n)
    def __str__(self):
        for _ in (): pass
        log.append(("str", self.n))
        return str(-self.n)
    def __abs__(self):
        for _ in (): pass
        log.append(("abs", self.n))
        return self.n
    def __hash__(self):
        for _ in (): pass
        log.append(("hash", self.n))
        return 10 - self.n

def keys():
    a, b, c = Item(3), Item(1), Item(2)
    s = [a, b, c]
    s.sort(key=len)
    return [[x.n for x in sorted([a, b, c], key=len)], [x.n for x in s], max(a, b, c, key=repr).n,
            min([a, b, c], key=str).n, [x.n for x in sorted((a, b, c), key=hash, reverse=True)],
            max([a, "zz", b], key=len) is a, min([c, a], key=abs).n]

expected = [[1, 2, 3], [1, 2, 3], 3, 1, [1, 2, 3], True, 2]
expected_log = [("len", 3), ("len", 1), ("len", 2), ("len", 3), ("len", 1), ("len", 2), ("repr", 3), ("repr", 1), ("repr", 2),
                ("str", 3), ("str", 1), ("str", 2), ("hash", 3), ("hash", 1), ("hash", 2), ("len", 3), ("len", 1),
                ("abs", 2), ("abs", 3)]
assert_eq(keys(), expected)
assert_eq(log, expected_log)
log.clear()

assert_eq([x.n for x in sorted([Item(2), Item(0)], key=len)], [0, 2])
assert_eq(log, [("len", 2), ("len", 0)])
log.clear()

def errors():
    out = []
    s = [Item(1), Item(-1), Item(2)]
    try: s.sort(key=len)
    except LookupError as e: out.append(e.args)
    out.append([x.n for x in s])
    try: max([Item(1), Item(-2)], key=len)
    except LookupError as e: out.append(e.args)
    return out

assert_eq(errors(), [("len",), [1, -1, 2], ("len",)])
assert_eq(log, [("len", 1), ("len", -1), ("len", 1), ("len", -2)])
