# spec: PLS-315 27.1.4, 27.1.6, 27.1.8, 7.7.6
# description: list(), tuple(), sum(), sorted(), dict() and next() of an
# instance of an enumerate, zip, map or filter subclass that overrides
# neither __iter__ nor __next__ take its items as its builtin iterator
# gives them, resuming the generators and calling the Python __next__,
# __getitem__ or function it takes from, in order; a subclass's Python
# __next__ or __iter__ is called instead. An error propagates, and
# next()'s default is returned once the iterator ends.
from harness import *

log = []
def gen(*items):
    for item in items:
        for _ in (): pass
        log.append(("gen", item))
        yield item

class It:
    def __init__(self, n): self.n = n
    def __iter__(self): return self
    def __next__(self):
        for _ in (): pass
        log.append(("it", self.n))
        if self.n <= 0: raise StopIteration
        self.n -= 1
        return self.n

class Seq:
    def __getitem__(self, i):
        log.append(("item", i))
        if i >= 2: raise IndexError(i)
        return i * 10

class E(enumerate): pass
class Z(zip): pass
class M(map): pass
class F(filter): pass
class N(enumerate):
    def __next__(self):
        log.append("N")
        return super().__next__()

def double(x):
    for _ in (): pass
    log.append(("double", x))
    return x * 2

def bad():
    yield 1
    raise KeyError("k")

def attempt(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))

def results():
    for _ in (): pass
    del log[:]
    e = E(gen("a"))
    out = [list(E(gen("x", "y"), 1)), tuple(Z(gen(1, 2), It(2))), sum(M(double, gen(1, 2))),
           sorted(F(None, Seq())), dict(E(It(1))), next(e), next(e, "end"),
           list(N(gen("n"))), attempt(lambda: list(E(bad())))]
    return out, list(log)

expected = ([[(1, "x"), (2, "y")], ((1, 1), (2, 0)), 6, [10], {0: 0}, (0, "a"), "end",
             [(0, "n")], ("KeyError", "'k'")],
            [("gen", "x"), ("gen", "y"), ("gen", 1), ("it", 2), ("gen", 2), ("it", 1),
             ("gen", 1), ("double", 1), ("gen", 2), ("double", 2),
             ("item", 0), ("item", 1), ("item", 2), ("it", 1), ("it", 0), ("gen", "a"),
             "N", ("gen", "n"), "N"])

assert_eq(results(), expected)
assert_eq(results(), expected)
