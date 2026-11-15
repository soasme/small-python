# spec: PLS-315 14.2, 25.5.4
# description: assigning a generator, or an iterator of a Python
# __next__, to a slice of a list runs the generator's body, which may
# loop, to its end after the target and the slice are evaluated, then
# replaces the slice with the items, as their list does: a step other
# than 1 requires as many items as the slice selects, an exception from
# the generator propagates leaving the list unchanged, and a chained
# assignment gives each target the same, exhausted, generator. Inside
# functions as at module level.
from harness import *

log = []

def items(*values):
    for v in values:
        for _ in (): pass
        log.append(v)
        yield v

class Counter:
    def __init__(self, n): self.n, self.i = n, 0
    def __iter__(self): return self
    def __next__(self):
        for _ in (): pass
        if self.i == self.n: raise StopIteration
        self.i += 1
        return self.i

def target(name, value):
    log.append(name)
    return value

def stores():
    a = [0, 1, 2, 3, 4]
    target("t", a)[target("s", 1):target("e", 4)] = items(7, 8)
    b = list(range(6))
    b[::2] = items(10, 20, 30)
    c = [0, 0]
    c[1:] = Counter(3)
    d = e = [1, 2]
    d[:] = e[0:1] = g = items(5, 6)
    return a, b, c, d, list(g)

expected = ([0, 7, 8, 4], [10, 1, 20, 3, 30, 5], [0, 1, 2, 3], [6], [])
assert_eq(stores(), expected)
assert_eq(log, ["t", "s", "e", 7, 8, 10, 20, 30, 5, 6])
log.clear()

m = [1, 2, 3]
m[1:2] = items(9, 9, 9)
assert_eq((m, log), ([1, 9, 9, 9, 3], [9, 9, 9]))

def raising():
    yield 1
    raise LookupError("gen")

def errors():
    out = []
    s = [1, 2, 3, 4]
    try: s[::2] = items(1)
    except ValueError as e: out.append(str(e))
    try: s[1:] = raising()
    except LookupError as e: out.append(e.args)
    out.append(s)
    return out

assert_eq(errors(), ["attempt to assign sequence of size 1 to extended slice of size 2", ("gen",), [1, 2, 3, 4]])
