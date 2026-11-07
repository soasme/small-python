# spec: PLS-315 27.1.1, 27.1.4, 27.1.5, 27.1.6, 27.1.8
# description: zip and map over generators, alone or with list, tuple and
# range iterators, take one item from each iterable in order for each of
# theirs, in loops, comprehensions and consumers, inside functions as at
# module level; the first iterable to end ends the zip, the items before
# it taken and dropped, and the next call starts again from the first
# iterable, as each call of enumerate, filter, map and zip asks their
# iterables again once they ended; an error in a generator ends the loop,
# and a StopIteration from map's function ends the map.
from harness import *

log = []

def gen(name, *items):
    for item in items:
        for _ in range(2): pass
        log.append((name, item))
        yield item

def twice(x):
    for _ in range(2): pass
    return 2 * x

def failing():
    yield 1
    raise KeyError("gen")

def stopping(x):
    if x > 1: raise StopIteration
    return x

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def zips():
    del log[:]
    out = [list(zip(gen("a", 1, 2, 3), gen("b", 4, 5))), list(log)]
    del log[:]
    total = 0
    for i, x in zip(range(10, 20), gen("c", 1, 2)):
        total += i * x
    out += [total, list(log)]
    del log[:]
    first = iter([7, 8, 6, 5])
    z = zip(first, gen("d", 1), (9, 9, 9))
    out += [next(z), error(lambda: next(z)), list(log), list(z), list(first)]
    first = iter([7, 8, 6, 5])
    z = zip(first, gen("d", 1))
    for pair in z: out.append(pair)
    out += [list(z), list(first)]
    del log[:]
    out += [[t for t in zip(gen("e", 1, 2), [3])], list(log)]
    out += [list(map(twice, gen("f", 1, 2))), list(map(str, gen("g", 3))), sum(map(abs, gen("h", -1, -2))),
            list(map(pow, gen("i", 2, 3), [3, 2, 1])), list(map(stopping, gen("j", 1, 2, 3))),
            sorted(zip(gen("k", 2, 1), "ab")), list(zip(gen("l"))), list(zip()),
            error(lambda: list(zip(failing(), [1, 2]))), error(lambda: list(zip([1], gen("m", 1), strict=True)) and
                                                                  list(zip([1, 2], gen("n", 1), strict=True)))]
    return out

expected = [[(1, 4), (2, 5)], [("a", 1), ("b", 4), ("a", 2), ("b", 5), ("a", 3)],
            32, [("c", 1), ("c", 2)],
            (7, 1, 9), ("StopIteration", ""), [("d", 1)], [], [5], (7, 1), [], [5],
            [(1, 3)], [("e", 1), ("e", 2)],
            [2, 4], ["3"], 3, [8, 9], [1], [(1, "b"), (2, "a")], [], [],
            ("KeyError", "'gen'"), ("ValueError", "zip() argument 2 is shorter than argument 1")]
assert_eq(zips(), expected)
del log[:]
assert_eq(list(zip(gen("x", 1, 2), gen("y", 3))), [(1, 3)])
assert_eq(log, [("x", 1), ("y", 3), ("x", 2)])

class Pauses:
    def __init__(self): self.n = 0
    def __iter__(self): return self
    def __next__(self):
        self.n += 1
        if self.n in (2, 4) or self.n > 5: raise StopIteration
        return self.n

def again(make):
    it = make(Pauses())
    return [list(it), list(it), list(it)]

assert_eq([again(lambda s: map(abs, s)), again(lambda s: filter(None, s)), again(enumerate), again(zip)],
          [[[1], [3], [5]], [[1], [3], [5]], [[(0, 1)], [(1, 3)], [(2, 5)]], [[(1,)], [(3,)], [(5,)]]])
