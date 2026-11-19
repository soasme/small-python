# spec: PLS-315 7.2.4, 26.4, 26.5.1
# description: tuples and lists holding dicts compare those dicts as
# dicts compare: each key of the left looked up in the right by its
# Python __eq__, then the values by theirs, in the left dict's order;
# so do such pairs inside dicts, in an in test of a list, and in an
# ordering's first equal items. Inside functions and generators as at
# module level.
from harness import *

log = []
class V:
    def __init__(self, v): self.v = v
    def __hash__(self): return 1
    def __eq__(self, o):
        for _ in (): pass
        log.append(("eq", self.v, getattr(o, "v", o)))
        return self.v == getattr(o, "v", o)

def run(f):
    del log[:]
    return f(), list(log)

def cases():
    return [run(lambda: ({V(1): 0},) == ({V(1): 0},)),
            run(lambda: ({1: V(2), V(3): 4},) == ({1: V(2), V(3): 4},)),
            run(lambda: [{V(5): {V(6): 1}}] != [{V(5): {V(6): 1}}]),
            run(lambda: ({V(7): 1}, 2) < ({V(7): 1}, 3)),
            run(lambda: ({V(8): 1},) in [0, ({V(8): 1},)]),
            run(lambda: {1: ({V(9): 1},)} == {1: ({V(9): 1},)}),
            run(lambda: ({V(10): 1},) == ({V(11): 1},))]

expected = [(True, [('eq', 1, 1)]),
            (True, [('eq', 3, 1), ('eq', 3, 1), ('eq', 2, 2), ('eq', 3, 1), ('eq', 3, 3)]),
            (False, [('eq', 5, 5), ('eq', 6, 6)]),
            (True, [('eq', 7, 7)]),
            (True, [('eq', 8, 8)]),
            (True, [('eq', 9, 9)]),
            (False, [('eq', 11, 10)])]
assert_eq(cases(), expected)

def gen():
    yield cases()
assert_eq(next(gen()), expected)
