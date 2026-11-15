# spec: PLS-315 19.3.26, 19.3.34, 25.1.4
# description: sorted(), min() and max() with a builtin key function over
# a list or tuple iterator, partly consumed or not, a set, a frozenset, a
# dict or its keys view call each instance item's Python __len__ or
# __repr__ once, in iteration order, each of which may loop, then order
# by the keys; a key's error propagates, and a consumed iterator gives
# only its remaining items. Inside functions as at module level.
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
        return "i%d" % self.n
    def __hash__(self): return self.n

def ns(items): return [i.n for i in items]

def sources():
    xs = [Item(3), Item(1), Item(2)]
    out = [ns(sorted(iter(xs), key=len)), max(iter(tuple(xs)), key=len).n, min(set(xs), key=repr).n]
    it = iter(xs); next(it)
    out.append(ns(sorted(it, key=len)))
    d = {Item(5): 0, Item(4): 1, Item(6): 2}
    del d[next(iter(d))]
    out += [ns(sorted(d, key=len)), ns(sorted(d.keys(), key=repr)), ns(sorted(frozenset(xs), key=len))]
    try: sorted(iter([Item(1), Item(-1)]), key=len)
    except LookupError as e: out.append(e.args)
    return out

expected = [[1, 2, 3], 3, 1, [1, 2], [4, 6], [4, 6], [1, 2, 3], ("len",)]
assert_eq(sources(), expected)
assert_eq(log[:6], [("len", 3), ("len", 1), ("len", 2), ("len", 3), ("len", 1), ("len", 2)])
assert_eq(log[-2:], [("len", 1), ("len", -1)])
log.clear()

xs = [Item(2), Item(1)]
assert_eq((ns(sorted(iter(xs), key=len)), max(iter(xs), key=repr).n), ([1, 2], 2))
assert_eq(log, [("len", 2), ("len", 1), ("repr", 2), ("repr", 1)])
