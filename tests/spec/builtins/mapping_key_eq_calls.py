# spec: PLS-315 26.1.2, 26.2, 25.5.2, 25.5.3
# description: == of two dicts or frozendicts, in either mix, looks each
# key of the left up in the right, comparing equal-hash keys by their
# Python __eq__; so do a list's or tuple's in, index() and count() of such
# a mapping among mappings, and a mapping inside a tuple; an exception
# propagates and an unequal key makes the mappings unequal.
from harness import *

log = []
class K:
    def __init__(self, n, result=True):
        self.n, self.result = n, result
    def __eq__(self, other):
        for _ in (): pass
        log.append(self.n)
        if self.result == "raise": raise ValueError(self.n)
        return self.result
    def __hash__(self): return 1
class V(K): pass
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, list(log)
def made(kind, key, value, result=True):
    return kind({K(key, result): V(value)})
def gen():
    yield frozendict({K(1): 0}) == frozendict({K(2): 0})
    yield [frozendict({K(3): 0})].index(frozendict({K(4): 0}))
assert_eq(run(lambda: made(dict, 1, 2) == made(dict, 3, 4)), (True, [3, 2]))
assert_eq(run(lambda: made(dict, 1, 2, False) == made(dict, 3, 4)), (True, [3, 2]))
assert_eq(run(lambda: made(dict, 1, 2, 'raise') != made(dict, 3, 4)), (False, [3, 2]))
assert_eq(run(lambda: (made(dict, 1, 2),) == (made(dict, 3, 4),)), (True, [3, 2]))
assert_eq(run(lambda: [made(dict, 1, 2)].index(made(dict, 3, 4))), (0, [3, 2]))
assert_eq(run(lambda: made(dict, 3, 4) in [made(dict, 1, 2)]), (True, [3, 2]))
assert_eq(run(lambda: [made(dict, 1, 2, False), made(dict, 5, 6)].count(made(dict, 3, 4))), (2, [3, 2, 3, 6]))
assert_eq(run(lambda: made(dict, 3, 4) in (made(dict, 1, 2, False),)), (True, [3, 2]))
assert_eq(run(lambda: made(dict, 1, 2) == made(frozendict, 3, 4)), (True, [3, 2]))
assert_eq(run(lambda: made(dict, 1, 2, False) == made(frozendict, 3, 4)), (True, [3, 2]))
assert_eq(run(lambda: made(dict, 1, 2, 'raise') != made(frozendict, 3, 4)), (False, [3, 2]))
assert_eq(run(lambda: (made(dict, 1, 2),) == (made(frozendict, 3, 4),)), (True, [3, 2]))
assert_eq(run(lambda: [made(dict, 1, 2)].index(made(frozendict, 3, 4))), (0, [3, 2]))
assert_eq(run(lambda: made(frozendict, 3, 4) in [made(dict, 1, 2)]), (True, [3, 2]))
assert_eq(run(lambda: [made(dict, 1, 2, False), made(dict, 5, 6)].count(made(frozendict, 3, 4))), (2, [3, 2, 3, 6]))
assert_eq(run(lambda: made(frozendict, 3, 4) in (made(dict, 1, 2, False),)), (True, [3, 2]))
assert_eq(run(lambda: made(frozendict, 1, 2) == made(dict, 3, 4)), (True, [3, 2]))
assert_eq(run(lambda: made(frozendict, 1, 2, False) == made(dict, 3, 4)), (True, [3, 2]))
assert_eq(run(lambda: made(frozendict, 1, 2, 'raise') != made(dict, 3, 4)), (False, [3, 2]))
assert_eq(run(lambda: (made(frozendict, 1, 2),) == (made(dict, 3, 4),)), (True, [3, 2]))
assert_eq(run(lambda: [made(frozendict, 1, 2)].index(made(dict, 3, 4))), (0, [3, 2]))
assert_eq(run(lambda: made(dict, 3, 4) in [made(frozendict, 1, 2)]), (True, [3, 2]))
assert_eq(run(lambda: [made(frozendict, 1, 2, False), made(frozendict, 5, 6)].count(made(dict, 3, 4))), (2, [3, 2, 3, 6]))
assert_eq(run(lambda: made(dict, 3, 4) in (made(frozendict, 1, 2, False),)), (True, [3, 2]))
assert_eq(run(lambda: made(frozendict, 1, 2) == made(frozendict, 3, 4)), (True, [3, 2]))
assert_eq(run(lambda: made(frozendict, 1, 2, False) == made(frozendict, 3, 4)), (True, [3, 2]))
assert_eq(run(lambda: made(frozendict, 1, 2, 'raise') != made(frozendict, 3, 4)), (False, [3, 2]))
assert_eq(run(lambda: (made(frozendict, 1, 2),) == (made(frozendict, 3, 4),)), (True, [3, 2]))
assert_eq(run(lambda: [made(frozendict, 1, 2)].index(made(frozendict, 3, 4))), (0, [3, 2]))
assert_eq(run(lambda: made(frozendict, 3, 4) in [made(frozendict, 1, 2)]), (True, [3, 2]))
assert_eq(run(lambda: [made(frozendict, 1, 2, False), made(frozendict, 5, 6)].count(made(frozendict, 3, 4))), (2, [3, 2, 3, 6]))
assert_eq(run(lambda: made(frozendict, 3, 4) in (made(frozendict, 1, 2, False),)), (True, [3, 2]))
assert_eq(run(lambda: frozendict({K(1): 1, K(2): 2}) == frozendict({K(3): 1, K(4): 2})), (True, [1, 3, 3]))
assert_eq(run(lambda: {K(1): 1} == {K(2): 1, K(3): 2}), (False, [2, 2]))
assert_eq(run(lambda: list(gen())), ([True, 0], [2, 4]))
