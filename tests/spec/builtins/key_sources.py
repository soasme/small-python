# spec: PLS-315 27
# description: sorted() with keywords takes all of a generator's, a
# map's or a Python iterator's items before the first key call, then
# calls the key on each in order; min() and max() call the key on each
# item as they take it, and return their default for no items; an
# unknown keyword raises TypeError before any item is taken, inside
# functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

def gen(n):
    for i in range(n):
        spin()
        log.append(("item", i))
        yield i

class Counter:
    def __init__(self, n): self.i, self.n = 0, n
    def __iter__(self): return self
    def __next__(self):
        spin()
        if self.i >= self.n: raise StopIteration
        self.i += 1
        log.append(("next", self.i))
        return self.i

def key(v):
    spin()
    log.append(("key", v))
    return -v

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    out = [sorted(gen(3), key=key), sorted(gen(2), reverse=True), sorted((x for x in gen(2)), key=str),
           min(gen(3), key=key), max(Counter(2), key=key), sorted(map(lambda v: v * 2, gen(2)), key=key),
           max(gen(2), default=7), max(gen(0), key=key, default=7), min((x for x in gen(2) if x > 5), key=key, default=9),
           error(lambda: max(gen(2), bogus=1)), error(lambda: sorted(gen(2), key=lambda v: 1 / v))]
    out.append(list(log))
    return out

expected = [[2, 1, 0], [1, 0], [0, 1], 2, 1, [2, 0], 1, 7, 9,
            ('TypeError', "max() got an unexpected keyword argument 'bogus'"), ('ZeroDivisionError', 'division by zero'),
            [('item', 0), ('item', 1), ('item', 2), ('key', 0), ('key', 1), ('key', 2), ('item', 0), ('item', 1), ('item', 0), ('item', 1), ('item', 0), ('key', 0), ('item', 1), ('key', 1), ('item', 2), ('key', 2), ('next', 1), ('key', 1), ('next', 2), ('key', 2), ('item', 0), ('item', 1), ('key', 0), ('key', 2), ('item', 0), ('item', 1), ('item', 0), ('item', 1), ('item', 0), ('item', 1)]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
