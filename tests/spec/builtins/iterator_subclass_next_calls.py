# spec: PLS-315 27.1.1, 27.1.4, 7.7.6
# description: list(), tuple(), sorted(), sum(), set(), str.join, a
# starred display, and dict(), dict.update() and frozendict() of its pairs,
# of an instance of a subclass of map, zip, filter or enumerate that keeps
# its builtin __iter__, which gives the instance, and defines __next__ take
# each item from that Python __next__, which may loop and call the
# builtin's by super(); its exception propagates, the items before it
# taken. Inside functions as at module level.
from harness import *

log = []

class M(map):
    def __next__(self):
        for _ in range(2): pass
        v = super().__next__()
        log.append(v)
        if v == 9: raise LookupError("m")
        return ("M", v)

class Z(zip):
    def __next__(self): return super().__next__()[::-1]

class F(filter):
    def __next__(self): return -super().__next__()

class E(enumerate):
    def __next__(self):
        i, v = super().__next__()
        return v * i

def t(f):
    try:
        r = f()
    except Exception as e:
        r = type(e).__name__ + ": " + str(e)
    out = (r, log[:])
    del log[:]
    return out

def update(source):
    d = {"q": 0}
    d.update(source)
    return d

def results():
    return [t(lambda: list(M(abs, [-1, -2]))), t(lambda: tuple(M(abs, [3]))), t(lambda: sorted(M(abs, [5, -4]))),
            t(lambda: sum(Z([1], [2]), ())), t(lambda: list(F(None, [0, 1, 2]))), t(lambda: list(E("ab"))),
            t(lambda: [*M(abs, [7])]), t(lambda: sorted(set(F(None, [3, 4])))), t(lambda: ",".join(map(str, E([2, 3])))),
            t(lambda: list(M(abs, [1, 9, 2]))), t(lambda: dict(Z(["k", "j"], [1, 2]))), t(lambda: update(Z([3], "c"))),
            t(lambda: dict(frozendict(Z([4], "d"), w=0))), t(lambda: dict(M(abs, [1, 9])))]

expected = [([('M', 1), ('M', 2)], [1, 2]), ((('M', 3),), [3]), ([('M', 4), ('M', 5)], [5, 4]), ((2, 1), []),
            ([-1, -2], []), (['', 'b'], []), ([('M', 7)], [7]), ([-4, -3], []), ('0,3', []), ('LookupError: m', [1, 9]),
            ({1: 'k', 2: 'j'}, []), ({'q': 0, 'c': 3}, []), ({'d': 4, 'w': 0}, []), ('LookupError: m', [1, 9])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
