# spec: PLS-315 7.7.1, 7.7.2, 27.1.1
# description: list, tuple, set, frozenset, sum, min, max, any, all, sorted
# and str.join take an instance's items through its class's Python
# __iter__, which may return the instance itself, whose __next__ loops,
# or be a generator function; inside functions as at module level, an
# __iter__ that returns no iterator or raises, and a __next__ that
# raises, end the call with that error.
from harness import *

class Counter:
    def __init__(self, n): self.n = n; self.i = 0
    def __iter__(self):
        for _ in range(2): pass
        return self
    def __next__(self):
        for _ in range(2): pass
        self.i += 1
        if self.i > self.n: raise StopIteration
        return self.i

class Bag:
    def __init__(self, *items): self.items = items
    def __iter__(self):
        for item in self.items:
            for _ in range(2): pass
            yield item

class Broken:
    def __iter__(self): return 1

class Raising:
    def __iter__(self): raise StopIteration("from iter")

class Failing:
    def __iter__(self): return self
    def __next__(self): raise KeyError("next")

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def consume():
    return [list(Counter(3)), tuple(Counter(2)), set(Counter(2)), frozenset(Bag(1, 1)),
            sum(Counter(3)), sum(Bag(1, 2), 10), min(Counter(3)), max(Bag(4, 9, 2)),
            any(Bag(0, 0)), all(Bag(1, 2)), sorted(Bag(3, 1, 2)), sorted(Counter(2)),
            ",".join(Bag("a", "b")), list(Bag()),
            error(lambda: list(Broken())), error(lambda: sorted(Broken())),
            error(lambda: sum(Raising())), error(lambda: tuple(Failing())),
            error(lambda: max(Bag()))]

expected = [[1, 2, 3], (1, 2), {1, 2}, frozenset({1}), 6, 13, 1, 9, False, True,
            [1, 2, 3], [1, 2], "a,b", [],
            ("TypeError", "Broken.__iter__() must return an iterator, not int"),
            ("TypeError", "Broken.__iter__() must return an iterator, not int"),
            ("StopIteration", "from iter"), ("KeyError", "'next'"),
            ("ValueError", "max() iterable argument is empty")]
assert_eq(consume(), expected)
assert_eq(list(Counter(2)) + sorted(Bag(2, 1)), [1, 2, 1, 2])
