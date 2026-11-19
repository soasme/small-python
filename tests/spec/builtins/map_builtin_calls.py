# spec: PLS-315 27.1.6, 19.3.34, 19.3.21
# description: map() of sorted(), min(), max(), isinstance() or sum() whose
# call reaches Python comparisons or an __instancecheck__ calls them in
# order, whether a loop, list(), next() or yield from takes its items;
# an error from the call propagates. Inside functions and generators as
# at module level.
from harness import *
log = []
class N:
    def __init__(self, n): self.n = n
    def __lt__(self, other):
        for _ in (): pass
        log.append(("lt", self.n, other.n))
        return self.n < other.n
    def __repr__(self): return "N%d" % self.n
class Meta(type):
    def __instancecheck__(cls, x):
        for _ in (): pass
        log.append(("check", x))
        return x == 1
class A(metaclass=Meta): pass
class S(list):
    def __add__(self, other):
        for _ in (): pass
        log.append(("add", list(self), other))
        return S(list(self) + list(other))
def run(f):
    del log[:]
    try: result = repr(f())
    except TypeError as error: result = ("TypeError", str(error))
    return result, list(log)
def looped():
    out = []
    for x in map(sorted, [[N(4), N(3)], [N(6), N(5)]]): out.append(x)
    return out
def delegated():
    yield from map(sorted, [[N(8), N(7)]])
def cases():
    return [run(lambda: next(map(sorted, [[N(2), N(1)]]))), run(looped), run(lambda: list(delegated())),
            run(lambda: list(map(isinstance, [1, 2], [A, A]))), run(lambda: list(map(min, [[N(10), N(9)]]))),
            run(lambda: list(map(max, [N(11)], [N(12)]))), run(lambda: list(map(sum, [[S([1]), [2]]], [S()]))),
            run(lambda: [len(x) for x in map(sorted, ["ba", "dc"])]), run(lambda: list(map(sorted, [[N(1), 2]]))),
            run(lambda: list(map(sorted, [1]))), run(lambda: next(map(sorted, []), "empty"))]
def gen():
    yield cases()
expected = [('[N1, N2]', [('lt', 1, 2)]),
            ('[[N3, N4], [N5, N6]]', [('lt', 3, 4), ('lt', 5, 6)]),
            ('[[N7, N8]]', [('lt', 7, 8)]),
            ('[True, False]', [('check', 1), ('check', 2)]),
            ('[N9]', [('lt', 9, 10)]),
            ('[N12]', [('lt', 11, 12)]),
            ('[[1, 2]]', [('add', [], [1]), ('add', [1], [2])]),
            ('[2, 2]', []),
            (('TypeError', "'<' not supported between instances of 'int' and 'N'"), []),
            (('TypeError', "'int' object is not iterable"), []),
            ("'empty'", [])]
assert_eq(cases(), expected)
assert_eq(next(gen()), expected)
def outer():
    return cases()
assert_eq(outer(), expected)
