# spec: PLS-315 13.3.4
# description: A call's starred argument takes a generator's or an
# instance's items through its class's Python __iter__ and __next__, in
# order among the other arguments, inside functions as at module level;
# an error in the generator, or an __iter__ returning no iterator, ends
# the call before the callee runs.
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

class Broken:
    def __iter__(self): return 1

def failing():
    yield 1
    raise KeyError("gen")

def called(*args, **kwargs):
    log.append("called")
    return args, kwargs

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def calls():
    del log[:]
    out = [called(*gen(1, 2)), called(0, *Bag(3, 4), *Counter(2), k=5), max(*gen(7, 9, 8)),
           called(*gen(), *[]), error(lambda: called(*failing())),
           error(lambda: called(*Broken())), error(lambda: called(*gen(6), *1))]
    return out + [list(log)]

expected = [((1, 2), {}), ((0, 3, 4, 1, 2), {"k": 5}), 9, ((), {}),
            ("KeyError", "'gen'"),
            ("TypeError", "Broken.__iter__() must return an iterator, not int"),
            ("TypeError", "Value after * must be an iterable, not int"),
            [1, 2, "called", "called", 7, 9, 8, "called", 6]]
assert_eq(calls(), expected)
assert_eq(called(*gen(1), *Bag(2)), ((1, 2), {}))
