# spec: PLS-315 13.2.1, 13.2.2, 7.7.1
# description: A starred item in a list, tuple or set display takes the
# items of a generator, or of an instance through its class's Python
# __iter__ returning the instance, whose __next__ loops, or a generator,
# in order among the other items, inside functions as at module level;
# an __iter__ that returns no iterator and a __next__ that raises end the
# display with that error.
from harness import *

def gen(n):
    for i in range(n):
        for _ in range(2): pass
        yield i

class Counter:
    def __init__(self, n): self.n = n; self.i = 0
    def __iter__(self): return self
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

def displays():
    c, b = Counter(2), Bag("x", "y")
    out = [[*gen(3)], (*c,), {*b}, [0, *gen(2), *Bag(7), 9], (*gen(1), *Counter(1)), [*Bag()], (*b, *b)]
    out += [error(lambda: [*Broken()]), error(lambda: (*Failing(), 1)), error(lambda: {0, *Broken()})]
    return out

expected = [[0, 1, 2], (1, 2), {"x", "y"}, [0, 0, 1, 7, 9], (0, 1), [], ("x", "y", "x", "y"),
            ("TypeError", "Broken.__iter__() must return an iterator, not int"), ("KeyError", "'next'"),
            ("TypeError", "Broken.__iter__() must return an iterator, not int")]
assert_eq(displays(), expected)
assert_eq([*Counter(2), *gen(1)], [1, 2, 0])
