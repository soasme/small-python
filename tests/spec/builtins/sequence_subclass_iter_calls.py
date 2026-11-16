# spec: PLS-315 7.7.6, 7.7.8
# description: list(), tuple(), sorted(), a starred display, str.join,
# sum(), min(), any(), enumerate(), zip(), set(), frozenset() and
# list.extend() of an instance of a list or tuple subclass whose class
# defines __iter__ take its items from that Python __iter__, which may
# loop, not from the builtin storage; the ones that make a list ask its
# __len__ after __iter__, and an exception from either propagates.
# Inside functions as at module level.
from harness import *

log = []

class Listed(list):
    def __iter__(self):
        for _ in range(2): pass
        log.append("iter")
        if getattr(self, "bad", False): raise LookupError("iter")
        return iter((7, 8))
    def __len__(self):
        log.append("len")
        return 1

class Tupled(tuple):
    def __iter__(self):
        for _ in range(2): pass
        log.append("titer")
        return iter((1, 2))

def t(f):
    try:
        r = f()
    except Exception as e:
        r = type(e).__name__ + ": " + str(e)
    out = (r, log[:])
    del log[:]
    return out

def results():
    L, T, bad = Listed([1, 2, 3]), Tupled((5, 6)), Listed()
    bad.bad = True
    extended = []
    return [t(lambda: list(L)), t(lambda: tuple(L)), t(lambda: sorted(L)), t(lambda: [*L]),
            t(lambda: ",".join(map(str, L))), t(lambda: sum(L)), t(lambda: min(L)), t(lambda: any(L)),
            t(lambda: list(enumerate(L))), t(lambda: list(zip(L, T))), t(lambda: sorted(set(T))),
            t(lambda: sorted(frozenset(L))), t(lambda: (extended.extend(L), extended)[1]), t(lambda: list(T)),
            t(lambda: max(T)), t(lambda: list(bad)), t(lambda: len(L))]

expected = [([7, 8], ['iter', 'len']), ((7, 8), ['iter']), ([7, 8], ['iter', 'len']), ([7, 8], ['iter', 'len']),
            ('7,8', ['iter']), (15, ['iter']), (7, ['iter']), (True, ['iter']), ([(0, 7), (1, 8)], ['iter']),
            ([(7, 1), (8, 2)], ['iter', 'titer']), ([1, 2], ['titer']), ([7, 8], ['iter']), ([7, 8], ['iter', 'len']),
            ([1, 2], ['titer']), (2, ['titer']), ('LookupError: iter', ['iter']), (1, ['len'])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
