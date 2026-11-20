# spec: PLS-315 19.3.20, 27.1.6
# description: iter(f, sentinel) of a generator's __next__ resumes the
# generator for each item, as calling __next__ does, until it yields an
# item equal to the sentinel, a Python __eq__ deciding, or ends; the
# generator's error propagates and ends the iterator, as its end does.
# list(), a comprehension, a for loop and next() agree.
from harness import *

log = []
class Eq:
    def __init__(self, v): self.v = v
    def __eq__(self, other):
        for _ in (): pass
        log.append(("eq", self.v, other))
        return self.v == other
    __hash__ = None

def gen(fail=False):
    for _ in (): pass
    yield 1
    log.append("after 1")
    yield 2
    if fail: raise KeyError("gen")
    yield 40
    yield 3

def results():
    for _ in (): pass
    del log[:]
    out = [list(iter(gen().__next__, 40)), [x for x in iter(gen().__next__, 40)], list(iter(gen().__next__, 99))]
    loop = []
    for x in iter(gen().__next__, 2): loop.append(x)
    out.append(loop)
    it = iter(gen().__next__, 40)
    out.append((next(it), next(it), next(it, "end"), next(it, "end")))
    it = iter(gen(True).__next__, 40)
    try: list(it)
    except KeyError as e: out.append(("KeyError", str(e)))
    out.append(next(it, "ended"))
    out.append(list(iter(gen().__next__, Eq(2))))
    return out, list(log)

expected = ([[1, 2], [1, 2], [1, 2, 40, 3], [1], (1, 2, "end", "end"), ("KeyError", "'gen'"), "ended", [1]],
            ["after 1", "after 1", "after 1", "after 1", "after 1", "after 1", ("eq", 2, 1), "after 1", ("eq", 2, 2)])

assert_eq(results(), expected)
assert_eq(results(), expected)
