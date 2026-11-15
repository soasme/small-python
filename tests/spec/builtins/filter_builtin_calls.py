# spec: PLS-315 27.1.5
# description: filter() of a builtin function or class, len, str or abs,
# calls each instance item's Python __len__, __str__ or __abs__ once as
# the filter reaches it, which may loop, keeping the items whose result
# is true, and tests the other items in C; an error from the method
# propagates, and the filter goes on after it. In a list, a for loop, a
# comprehension and next(), inside functions as at module level.
from harness import *

log = []

class Item:
    def __init__(self, n): self.n = n
    def __len__(self):
        for _ in (): pass
        log.append(("len", self.n))
        if self.n < 0: raise LookupError("len")
        return self.n
    def __str__(self):
        for _ in (): pass
        log.append(("str", self.n))
        return "x" * self.n
    def __abs__(self):
        for _ in (): pass
        log.append(("abs", self.n))
        return self.n

def kept():
    xs = [Item(1), "", Item(0), "a", Item(2), []]
    out = [[x if isinstance(x, str) else x.n for x in filter(len, xs)]]
    for x in filter(str, [Item(0), 0, Item(3)]): out.append(x if not isinstance(x, Item) else x.n)
    out.append([x.n for x in filter(abs, [Item(4), Item(0)])])
    it = filter(len, [Item(0), Item(5)])
    out.append(next(it).n)
    out.append(next(it, "end"))
    return out

expected = [[1, "a", 2], 0, 3, [4], 5, "end"]
expected_log = [("len", 1), ("len", 0), ("len", 2), ("str", 0), ("str", 3), ("abs", 4), ("abs", 0), ("len", 0), ("len", 5)]
assert_eq(kept(), expected)
assert_eq(log, expected_log)
log.clear()

assert_eq([x.n for x in filter(len, [Item(0), Item(7)])], [7])
assert_eq(log, [("len", 0), ("len", 7)])
log.clear()

def errors():
    it = filter(len, [Item(1), Item(-1), Item(2)])
    out = [next(it).n]
    try: next(it)
    except LookupError as e: out.append(e.args)
    out.append(next(it).n)
    return out

assert_eq(errors(), [1, ("len",), 2])
assert_eq(log, [("len", 1), ("len", -1), ("len", 2)])
