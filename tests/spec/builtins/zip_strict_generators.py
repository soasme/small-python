# spec: PLS-315 27.1.6, 27.1.8, 27.1.4
# description: zip(strict=True) and map(strict=True) over generators
# resume each, which may loop, for its item in order, in a loop, a
# consumer, dict() or next(); when the first iterable ends, each later one
# is asked in turn and must end too, else the ValueError names it as longer;
# a later one ending first is shorter. The first's return value is dropped
# from next(); an error from a generator propagates. Inside functions as at
# module level.
from harness import *

log = []

def gen(name, *items, ret=None):
    for item in items:
        for _ in range(2): pass
        log.append((name, item))
        yield item
    log.append((name, "end"))
    return ret
class It:
    def __init__(self, n): self.n = n
    def __iter__(self): return self
    def __next__(self):
        for _ in range(2): pass
        log.append(("it", self.n))
        if self.n <= 0: raise StopIteration
        self.n -= 1
        return self.n
def bad():
    yield 1
    raise KeyError("k")
def run(f):
    del log[:]
    try:
        r = f()
    except StopIteration as e:
        r = ("StopIteration", e.args)
    except (ValueError, KeyError) as e:
        r = (type(e).__name__, str(e))
    return r, list(log)
def loop(it):
    out = []
    for x in it:
        log.append("x"); out.append(x)
    return out
def results():
    out = [run(lambda: list(zip(gen("a", 1, 2), gen("b", 3, 4), strict=True))),
           run(lambda: list(zip(gen("a", 1, 2), gen("b", 3), strict=True))),
           run(lambda: list(zip(gen("a", 1), gen("b", 3, 4), strict=True))),
           run(lambda: list(zip(gen("a", 1), gen("b", 3), gen("c", 5, 6), strict=True))),
           run(lambda: list(zip(gen("a", 1), [3], gen("c", 5), strict=True))),
           run(lambda: list(zip(gen("a", 1, ret=9), [3, 4], strict=True))),
           run(lambda: list(zip([1, 2], gen("b", 3), strict=True))),
           run(lambda: list(zip([1], gen("b", 3, 4), strict=True))),
           run(lambda: list(zip(gen("a", 1), It(1), gen("c", 5), strict=True))),
           run(lambda: list(zip(gen("a", 1), It(2), strict=True))),
           run(lambda: list(zip(gen("a", 1, 2), [3], strict=True))),
           run(lambda: list(zip(gen("a"), map(int, ["x"]), strict=True))),
           run(lambda: list(zip(gen("a", 1), bad(), strict=True))),
           run(lambda: list(zip(gen("a"), bad(), strict=True))),
           run(lambda: loop(zip(gen("a", 1, 2), gen("b", 3), strict=True))),
           run(lambda: loop(zip(gen("a", 1), gen("b", 3), gen("c", 5, 6), strict=True))),
           run(lambda: dict(zip(gen("a", 1), gen("b", 3, 4), strict=True))),
           run(lambda: list(map(pow, gen("a", 2, 3), gen("b", 1), strict=True))),
           run(lambda: list(map(pow, gen("a", 2), gen("b", 1, 2), strict=True))),
           run(lambda: list(map(pow, gen("a", 2), gen("b", 1), gen("c", 1, 2), strict=True))),
           run(lambda: sum(x for x, _ in zip(gen("a", 1, 2), gen("b", 3, 4), strict=True)))]
    z = zip(gen("a", 1, ret=7), gen("b", 3, ret=8), strict=True)
    out += [run(lambda: next(z)), run(lambda: next(z)), run(lambda: next(z)), run(lambda: next(z, "d"))]
    z = zip(gen("a", 1), gen("b", 3, 4), strict=True)
    out += [run(lambda: next(z)), run(lambda: next(z)), run(lambda: next(z, "d"))]
    z = zip(gen("a", 1, 2), gen("b", 3), strict=True)
    out += [run(lambda: next(z)), run(lambda: next(z)), run(lambda: next(z, "d"))]
    return out

expected = [([(1, 3), (2, 4)], [('a', 1), ('b', 3), ('a', 2), ('b', 4), ('a', 'end'), ('b', 'end')]),
            (('ValueError', 'zip() argument 2 is shorter than argument 1'), [('a', 1), ('b', 3), ('a', 2), ('b', 'end')]),
            (('ValueError', 'zip() argument 2 is longer than argument 1'), [('a', 1), ('b', 3), ('a', 'end'), ('b', 4)]),
            (('ValueError', 'zip() argument 3 is longer than arguments 1-2'), [('a', 1), ('b', 3), ('c', 5), ('a', 'end'), ('b', 'end'), ('c', 6)]),
            ([(1, 3, 5)], [('a', 1), ('c', 5), ('a', 'end'), ('c', 'end')]),
            (('ValueError', 'zip() argument 2 is longer than argument 1'), [('a', 1), ('a', 'end')]),
            (('ValueError', 'zip() argument 2 is shorter than argument 1'), [('b', 3), ('b', 'end')]),
            (('ValueError', 'zip() argument 2 is longer than argument 1'), [('b', 3), ('b', 4)]),
            ([(1, 0, 5)], [('a', 1), ('it', 1), ('c', 5), ('a', 'end'), ('it', 0), ('c', 'end')]),
            (('ValueError', 'zip() argument 2 is longer than argument 1'), [('a', 1), ('it', 2), ('a', 'end'), ('it', 1)]),
            (('ValueError', 'zip() argument 2 is shorter than argument 1'), [('a', 1), ('a', 2)]),
            (('ValueError', "invalid literal for int() with base 10: 'x'"), [('a', 'end')]),
            (('KeyError', "'k'"), [('a', 1), ('a', 'end')]),
            (('ValueError', 'zip() argument 2 is longer than argument 1'), [('a', 'end')]),
            (('ValueError', 'zip() argument 2 is shorter than argument 1'), [('a', 1), ('b', 3), 'x', ('a', 2), ('b', 'end')]),
            (('ValueError', 'zip() argument 3 is longer than arguments 1-2'), [('a', 1), ('b', 3), ('c', 5), 'x', ('a', 'end'), ('b', 'end'), ('c', 6)]),
            (('ValueError', 'zip() argument 2 is longer than argument 1'), [('a', 1), ('b', 3), ('a', 'end'), ('b', 4)]),
            (('ValueError', 'map() argument 2 is shorter than argument 1'), [('a', 2), ('b', 1), ('a', 3), ('b', 'end')]),
            (('ValueError', 'map() argument 2 is longer than argument 1'), [('a', 2), ('b', 1), ('a', 'end'), ('b', 2)]),
            (('ValueError', 'map() argument 3 is longer than arguments 1-2'), [('a', 2), ('b', 1), ('c', 1), ('a', 'end'), ('b', 'end'), ('c', 2)]),
            (3, [('a', 1), ('b', 3), ('a', 2), ('b', 4), ('a', 'end'), ('b', 'end')]),
            ((1, 3), [('a', 1), ('b', 3)]),
            (('StopIteration', ()), [('a', 'end'), ('b', 'end')]),
            (('StopIteration', ()), []),
            ('d', []),
            ((1, 3), [('a', 1), ('b', 3)]),
            (('ValueError', 'zip() argument 2 is longer than argument 1'), [('a', 'end'), ('b', 4)]),
            ('d', [('b', 'end')]),
            ((1, 3), [('a', 1), ('b', 3)]),
            (('ValueError', 'zip() argument 2 is shorter than argument 1'), [('a', 2), ('b', 'end')]),
            ('d', [('a', 'end')])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
