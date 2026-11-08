# spec: PLS-315 7.8.3, 13.10
# description: in and not in over a generator, or an instance whose class
# has a Python __iter__ and no __contains__, take its items until one is
# the sought object or equal to it, leaving the rest untaken, inside
# functions as at module level; an error in the items ends the test, an
# __iter__ returning no iterator raises TypeError, and so does a
# __contains__ of None. An __iter__ that loops is called once, first; a
# TypeError it raises names the container, and other errors propagate.
from harness import *

log = []

def gen(*items):
    for item in items:
        for _ in range(2): pass
        log.append(item)
        yield item

class Bag:
    def __init__(self, *items): self.items = items
    def __iter__(self):
        for item in self.items:
            for _ in range(2): pass
            yield item

class Counter:
    def __init__(self, n): self.n = n; self.i = 0
    def __iter__(self): return self
    def __next__(self):
        for _ in range(2): pass
        self.i += 1
        if self.i > self.n: raise StopIteration
        return self.i

class Listed:
    def __init__(self, *items): self.items = items
    def __iter__(self):
        for _ in range(2): pass
        log.append("iter")
        return iter(self.items)

class Refuses:
    def __iter__(self):
        for _ in range(2): pass
        raise TypeError("refused")

class Raises:
    def __iter__(self): raise KeyError("iter")

class Broken:
    def __iter__(self): return 1

class Closed(Bag):
    __contains__ = None

class Same:
    def __eq__(self, other): return True

def failing():
    yield 1
    raise KeyError("gen")

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def tests():
    del log[:]
    rest = gen(1, 2, 3, 4)
    nan = float("nan")
    counter = Counter(5)
    out = [2 in rest, list(rest), 9 in gen(1, 2), 9 not in gen(1), 1 not in gen(1),
           3 in counter, counter.i, 7 in Counter(3), "b" in Bag("a", "b"), "z" not in Bag(),
           nan in gen(nan), Same() in gen(5), 1 in gen(0) in [False],
           error(lambda: 2 in failing()), error(lambda: 1 in Broken()),
           error(lambda: 1 in Closed(1)),
           2 in Listed(1, 2), 5 not in Listed(), error(lambda: 1 in Refuses()), error(lambda: 1 in Raises())]
    return out + [list(log)]

expected = [True, [3, 4], False, True, False, True, 3, False, True, True, True, True, False,
            ("KeyError", "'gen'"),
            ("TypeError", "argument of type 'Broken' is not a container or iterable"),
            ("TypeError", "'Closed' object is not a container"),
            True, True, ("TypeError", "argument of type 'Refuses' is not a container or iterable"),
            ("KeyError", "'iter'")]
result = tests()
assert_eq(result[:-1], expected)
assert_eq(result[-1][:4], [1, 2, 3, 4])
assert_eq(4 in gen(3, 4) and 2 not in Bag(1, 3), True)
spent = gen(1)
assert_eq([list(spent), 1 in spent, 1 not in spent], [[1], False, True])
