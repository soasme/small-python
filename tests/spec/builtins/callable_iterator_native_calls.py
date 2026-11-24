# spec: PLS-315 27.1.3, 13.10
# description: iter(f, sentinel) of a builtin callable, a bound __next__ or
# a builtin method, compares each item with the sentinel as it is made:
# the sentinel's or item's Python __eq__ runs once per item, and the truth
# of an instance it returns is that instance's Python __bool__, or its
# __len__ when it has no __bool__; a __bool__ returning a non-bool or
# raising propagates. In a list, a comprehension, yield from and next().
from harness import *

log = []

class Truth:
    def __init__(self, v): self.v = v
    def __bool__(self):
        for _ in (): pass
        log.append(("bool", self.v))
        if self.v is None: raise LookupError("bool")
        return self.v

class Size:
    def __init__(self, n): self.n = n
    def __len__(self):
        for _ in (): pass
        log.append(("len", self.n))
        return self.n

class Stop:
    def __init__(self, at): self.at = at
    def __eq__(self, other):
        for _ in (): pass
        log.append(("eq", other))
        return Truth(other == self.at)

class StopLen:
    def __eq__(self, other):
        for _ in (): pass
        log.append(("eq", other))
        return Size(int(other == 2))

class Item:
    def __init__(self, n): self.n = n
    def __eq__(self, other):
        for _ in (): pass
        log.append(("item", self.n))
        return Truth(self.n == other)

def run():
    out = [list(iter(iter([1, 2, 3]).__next__, Stop(3)))]
    out.append([x for x in iter(iter([0, 2]).__next__, StopLen())])
    def gen():
        yield from iter(iter([5, 6]).__next__, Stop(6))
    out.append(list(gen()))
    it = iter(iter([7, 8]).__next__, Stop(8))
    out.append(next(it))
    out.append([i.n for i in iter(iter([Item(1), Item(4)]).__next__, 4)])
    return out

assert_eq(run(), [[1, 2], [0], [5], 7, [1]])
assert_eq(log, [("eq", 1), ("bool", False), ("eq", 2), ("bool", False), ("eq", 3), ("bool", True),
                ("eq", 0), ("len", 0), ("eq", 2), ("len", 1),
                ("eq", 5), ("bool", False), ("eq", 6), ("bool", True),
                ("eq", 7), ("bool", False),
                ("item", 1), ("bool", False), ("item", 4), ("bool", True)])
del log[:]

class Wrong:
    def __eq__(self, other): return Truth(1)
assert_raises(TypeError, list, iter(iter([1]).__next__, Wrong()))
class Raises:
    def __eq__(self, other): return Truth(None)
assert_raises(LookupError, list, iter(iter([1]).__next__, Raises()))
assert_eq(log, [("bool", 1), ("bool", None)])
