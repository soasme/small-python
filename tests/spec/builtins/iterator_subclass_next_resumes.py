# spec: PLS-315 27.1.4, 27.1.8, 19.3.27, 27.1.1
# description: next() of an enumerate or zip subclass's instance, with or
# without a default, a subclass's Python __next__ calling
# super().__next__(), and the builtin's __next__ called on a plain
# enumerate, zip or map, bound or given it, resume the generators it
# takes from in order; at the end next() returns its default or raises
# StopIteration, and an error of the generator propagates.
from harness import *

log = []
def gen(*items):
    for item in items:
        for _ in (): pass
        log.append(("gen", item))
        yield item

class E(enumerate): pass
class Z(zip): pass
class N(enumerate):
    def __next__(self):
        log.append("N")
        return super().__next__()

def bad():
    yield 1
    raise KeyError("k")

def attempt(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))

def results():
    for _ in (): pass
    del log[:]
    e, z, n = E(gen("a")), Z(gen(1), gen(2)), N(gen("n"))
    b = E(bad())
    plain = enumerate(gen("p", "q"))
    out = [next(e), next(e, "end"), attempt(lambda: next(e)), next(z), next(n), attempt(lambda: next(n)),
           next(b), attempt(lambda: next(b)),
           plain.__next__(), enumerate.__next__(plain), map(abs, gen(-3)).__next__(), zip(gen(4)).__next__()]
    return out, list(log)

expected = ([(0, "a"), "end", ("StopIteration", ""), (1, 2), (0, "n"), ("StopIteration", ""),
             (0, 1), ("KeyError", "'k'"),
             (0, "p"), (1, "q"), 3, (4,)],
            [("gen", "a"), ("gen", 1), ("gen", 2), "N", ("gen", "n"), "N",
             ("gen", "p"), ("gen", "q"), ("gen", -3), ("gen", 4)])

assert_eq(results(), expected)
assert_eq(results(), expected)
