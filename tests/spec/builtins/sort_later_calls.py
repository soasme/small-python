# spec: PLS-315 25.1.4, 25.5.3
# description: a sort whose first comparison calls no Python method still
# calls those of later pairs, in the order a stable merge sort compares
# them: items of tuples nested in tuples, an instance with only a
# reflected method, and a pair whose first items are plain values. In
# functions and generators as at module level.
from harness import *

log = []
class P:
    def __init__(self, v): self.v = v
    def __eq__(self, o):
        for _ in (): pass
        log.append(("eq", self.v, o.v))
        return self.v == o.v
    def __lt__(self, o):
        for _ in (): pass
        log.append(("lt", self.v, o.v))
        return self.v < o.v
class R:
    def __init__(self, v): self.v = v
    def __gt__(self, o):
        for _ in (): pass
        log.append(("gt", self.v, o.v))
        return self.v > o.v

def run(items):
    del log[:]
    out = sorted(items)
    return [repr_of(x) for x in out], list(log)

def repr_of(x):
    if isinstance(x, tuple): return tuple(repr_of(i) for i in x)
    return getattr(x, "v", x)

def cases():
    return [run([(0, P(2)), (1, P(3)), (1, P(1)), (0, P(0))]),
            run([((1, P(2)),), ((1, P(1)),), ((0, P(5)),)]),
            run([3, R(1), R(0)][1:]),
            run([(2, 0), (1, 0), (1, P(4)), (1, P(3))][2:] + [(1, P(1))])]

expected = [([(0, 0), (0, 2), (1, 1), (1, 3)], [('eq', 1, 3), ('lt', 1, 3), ('eq', 1, 3), ('lt', 1, 3), ('eq', 0, 2), ('lt', 0, 2)]), ([((0, 5),), ((1, 1),), ((1, 2),)], [('eq', 1, 2), ('eq', 1, 2), ('lt', 1, 2)]), ([0, 1], [('gt', 1, 0)]), ([(1, 1), (1, 3), (1, 4)], [('eq', 3, 4), ('lt', 3, 4), ('eq', 1, 3), ('lt', 1, 3)])]
assert_eq(cases(), expected)

def gen():
    yield cases()
assert_eq(next(gen()), expected)
