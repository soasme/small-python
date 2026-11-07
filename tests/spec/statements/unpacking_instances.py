# spec: PLS-315 7.7.1, 7.7.2, 14.2
# description: A target list unpacks an instance through its class's
# Python __iter__, returning the instance, whose __next__ loops, or a
# generator; inside functions as at module level, with starred targets
# and chained targets, and with the errors of a wrong count, of an
# __iter__ that returns no iterator and of a __next__ that raises.
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

class Failing:
    def __iter__(self): return self
    def __next__(self): raise KeyError("next")

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def two(v):
    a, b = v
    return a, b

def star(v):
    a, *b = v
    return a, b

def unpack():
    out = [two(Counter(2)), two(Bag("x", "y")), star(Counter(3)), star(Bag(1))]
    [a, b] = Counter(2)
    x = (c, d) = Bag(5, 6)
    out += [(a, b), (c, d), type(x).__name__]
    out += [error(lambda: two(Counter(3))), error(lambda: two(Bag(1))), error(lambda: star(Bag())),
            error(lambda: two(Broken())), error(lambda: two(Failing()))]
    return out

expected = [(1, 2), ("x", "y"), (1, [2, 3]), (1, []), (1, 2), (5, 6), "Bag",
            ("ValueError", "too many values to unpack (expected 2)"),
            ("ValueError", "not enough values to unpack (expected 2, got 1)"),
            ("ValueError", "not enough values to unpack (expected at least 1, got 0)"),
            ("TypeError", "Broken.__iter__() must return an iterator, not int"),
            ("KeyError", "'next'")]
assert_eq(unpack(), expected)
p, q = Counter(2)
assert_eq((p, q), (1, 2))
