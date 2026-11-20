# spec: PLS-315 19.3.26, 7.7.1
# description: max() and min() of one iterable with a key or default
# keyword take its iterator from its class's Python __iter__ first, a
# generator function's too, then each item and its key in turn; a
# non-iterator from __iter__ or its exception raises before any key,
# an empty source gives the default or raises; inside functions,
# comprehensions and generators too.
from harness import assert_eq

log = []
class It:
    def __init__(self, n): self.n = n
    def __iter__(self):
        for _ in (): pass
        log.append(('iter', self.n))
        return iter(range(self.n))
class Gen:
    def __iter__(self):
        log.append('gen')
        yield 3; yield 1
class Bad:
    def __iter__(self):
        for _ in (): pass
        return 5
class Raise:
    def __iter__(self):
        for _ in (): pass
        raise LookupError('it')
class Next:
    def __init__(self): self.i = 0
    def __iter__(self):
        for _ in (): pass
        log.append('self'); return self
    def __next__(self):
        for _ in (): pass
        self.i += 1
        if self.i > 3: raise StopIteration
        log.append(('next', self.i)); return self.i
def key(v):
    for _ in (): pass
    log.append(('key', v)); return -v
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
cases = [lambda: max(It(3), key=key), lambda: min(It(3), key=key), lambda: max(It(0), key=key, default=7), lambda: max(It(0), default=7),
         lambda: max(It(0), key=key), lambda: min(Gen(), key=key), lambda: max(Bad(), key=key), lambda: min(Raise(), default=1),
         lambda: max(Next(), key=key), lambda: min(It(2), key=None), lambda: max(It(2), key=lambda v: 1 / v),
         lambda: [max(It(2), key=key) for _ in range(2)]]
EXPECTED = [
    (0, [('iter', 3), ('key', 0), ('key', 1), ('key', 2)]),
    (2, [('iter', 3), ('key', 0), ('key', 1), ('key', 2)]),
    (7, [('iter', 0)]),
    (7, [('iter', 0)]),
    (('ValueError', 'max() iterable argument is empty'), [('iter', 0)]),
    (3, ['gen', ('key', 3), ('key', 1)]),
    (('TypeError', 'Bad.__iter__() must return an iterator, not int'), []),
    (('LookupError', 'it'), []),
    (1, ['self', ('next', 1), ('key', 1), ('next', 2), ('key', 2), ('next', 3), ('key', 3)]),
    (0, [('iter', 2)]),
    (('ZeroDivisionError', 'division by zero'), [('iter', 2)]),
    ([0, 0], [('iter', 2), ('key', 0), ('key', 1), ('iter', 2), ('key', 0), ('key', 1)]),
]
assert_eq(len(cases), len(EXPECTED))
for i, (f, expected) in enumerate(zip(cases, EXPECTED)):
    assert_eq(run(f), expected, str(i))
def inside(): return [run(f) for f in cases]
assert_eq(inside(), EXPECTED)
def g(): yield max(It(2), key=key)
assert_eq(run(lambda: list(g())), ([0], [('iter', 2), ('key', 0), ('key', 1)]))
