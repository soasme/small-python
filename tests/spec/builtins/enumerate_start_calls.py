# spec: PLS-315 27.1.4, 7.5.3
# description: enumerate() given a start with a Python __index__ that may
# loop converts it, by position or keyword, before it calls iter() of
# the iterable, whose Python __iter__ then runs; either's exception
# propagates, and the count goes on from the start's int. Inside
# functions as at module level.
from harness import *

log = []
class I:
    def __iter__(self):
        for _ in (): pass
        log.append("iter")
        return iter([7, 8])
class B:
    def __iter__(self):
        for _ in (): pass
        log.append("iter")
        raise LookupError("it")
class N:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in (): pass
        log.append(("index", self.v))
        if self.v is None: raise KeyError("n")
        return self.v
class E(enumerate): pass
def t(f):
    try: r = f()
    except Exception as e: r = type(e).__name__ + ": " + str(e)
    out = (r, log[:]); del log[:]; return out
def results():
    return [t(lambda: list(enumerate(I(), N(3)))), t(lambda: list(enumerate([1], N(-2)))), t(lambda: list(enumerate(I(), start=N(1)))),
            t(lambda: list(enumerate(iterable=I(), start=N(1)))), t(lambda: enumerate(B(), N(1))), t(lambda: enumerate(I(), N(None))),
            t(lambda: list(enumerate(I(), N(1 << 70)))), t(lambda: list(E(I(), N(2)))), t(lambda: enumerate(I(), N(1), 3)),
            t(lambda: enumerate(I(), N("s"))), t(lambda: list(enumerate("ab", N(1)))),
            t(lambda: direct())]

def direct():
    a = list(enumerate(I(), N(4))); b = list(enumerate(I(), start=N(5)))
    return a, b

expected = [([(3, 7), (4, 8)], [('index', 3), 'iter']), ([(-2, 1)], [('index', -2)]),
            ([(1, 7), (2, 8)], [('index', 1), 'iter']), ([(1, 7), (2, 8)], [('index', 1), 'iter']),
            ('LookupError: it', [('index', 1), 'iter']), ("KeyError: 'n'", [('index', None)]),
            ([(1180591620717411303424, 7), (1180591620717411303425, 8)], [('index', 1180591620717411303424), 'iter']),
            ([(2, 7), (3, 8)], [('index', 2), 'iter']),
            ('TypeError: enumerate() takes at most 2 arguments (3 given)', []),
            ('TypeError: N.__index__() must return an int, not str', [('index', 's')]),
            ([(1, 'a'), (2, 'b')], [('index', 1)]),
            (([(4, 7), (5, 8)], [(5, 7), (6, 8)]), [('index', 4), 'iter', ('index', 5), 'iter'])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
