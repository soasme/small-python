# spec: PLS-315 25.5.2, 25.5.3, 26.1.2, 26.2
# description: index(), count() and remove() of a list or tuple compare
# each item, first, with the value searched; an item that is a tuple,
# list, dict or frozendict like the value compares their items or values
# by their Python __eq__ in order, nested either way; the first equal item
# answers, an exception propagates, and index's bounds limit the items.
from harness import *

log = []
class E:
    def __init__(self, n, result=True):
        self.n, self.result = n, result
    def __eq__(self, other):
        for _ in (): pass
        log.append(self.n)
        if self.result == "raise": raise ValueError(self.n)
        return self.result
    __hash__ = object.__hash__
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, list(log)
def removed(items, x):
    items.remove(x)
    return len(items)
KINDS = {"tuple": lambda n, r=True: (E(n, r),), "frozendict": lambda n, r=True: frozendict({1: E(n, r)}),
         "list": lambda n, r=True: [E(n, r)], "dict": lambda n, r=True: {1: E(n, r)}}
def gen():
    yield [(E(1),)].index((E(2),))
    yield [frozendict({1: E(3)})].count(frozendict({1: E(4)}))
assert_eq(run(lambda: [KINDS["tuple"](1, False), KINDS["tuple"](2), KINDS["tuple"](3)].index(KINDS["tuple"](4))), (1, [1, 2]))
assert_eq(run(lambda: [KINDS["tuple"](1, False), KINDS["tuple"](2), KINDS["tuple"](3)].count(KINDS["tuple"](4))), (2, [1, 2, 3]))
assert_eq(run(lambda: (KINDS["tuple"](1, False), KINDS["tuple"](2)).index(KINDS["tuple"](4))), (1, [1, 2]))
assert_eq(run(lambda: (KINDS["tuple"](1, False), KINDS["tuple"](2)).count(KINDS["tuple"](4))), (1, [1, 2]))
assert_eq(run(lambda: [KINDS["tuple"](1, False), KINDS["tuple"](2, False)].index(KINDS["tuple"](4))), (('ValueError', 'list.index(x): x not in list'), [1, 2]))
assert_eq(run(lambda: [KINDS["tuple"](1, 'raise'), KINDS["tuple"](2)].count(KINDS["tuple"](4))), (('ValueError', '1'), [1]))
assert_eq(run(lambda: [3, KINDS["tuple"](2)].index(KINDS["tuple"](4), 1)), (1, [2]))
assert_eq(run(lambda: removed([KINDS["tuple"](1, False), KINDS["tuple"](2), KINDS["tuple"](3)], KINDS["tuple"](4))), (2, [1, 2]))
assert_eq(run(lambda: [KINDS["tuple"](1, False), 5, KINDS["tuple"](2)].index(KINDS["tuple"](4))), (2, [1, 2]))
assert_eq(run(lambda: [KINDS["tuple"](1), KINDS["tuple"](2)].index(KINDS["tuple"](4), 1, 2)), (1, [2]))
assert_eq(run(lambda: [KINDS["frozendict"](1, False), KINDS["frozendict"](2), KINDS["frozendict"](3)].index(KINDS["frozendict"](4))), (1, [1, 2]))
assert_eq(run(lambda: [KINDS["frozendict"](1, False), KINDS["frozendict"](2), KINDS["frozendict"](3)].count(KINDS["frozendict"](4))), (2, [1, 2, 3]))
assert_eq(run(lambda: (KINDS["frozendict"](1, False), KINDS["frozendict"](2)).index(KINDS["frozendict"](4))), (1, [1, 2]))
assert_eq(run(lambda: (KINDS["frozendict"](1, False), KINDS["frozendict"](2)).count(KINDS["frozendict"](4))), (1, [1, 2]))
assert_eq(run(lambda: [KINDS["frozendict"](1, False), KINDS["frozendict"](2, False)].index(KINDS["frozendict"](4))), (('ValueError', 'list.index(x): x not in list'), [1, 2]))
assert_eq(run(lambda: [KINDS["frozendict"](1, 'raise'), KINDS["frozendict"](2)].count(KINDS["frozendict"](4))), (('ValueError', '1'), [1]))
assert_eq(run(lambda: [3, KINDS["frozendict"](2)].index(KINDS["frozendict"](4), 1)), (1, [2]))
assert_eq(run(lambda: removed([KINDS["frozendict"](1, False), KINDS["frozendict"](2), KINDS["frozendict"](3)], KINDS["frozendict"](4))), (2, [1, 2]))
assert_eq(run(lambda: [KINDS["frozendict"](1, False), 5, KINDS["frozendict"](2)].index(KINDS["frozendict"](4))), (2, [1, 2]))
assert_eq(run(lambda: [KINDS["frozendict"](1), KINDS["frozendict"](2)].index(KINDS["frozendict"](4), 1, 2)), (1, [2]))
assert_eq(run(lambda: [KINDS["list"](1, False), KINDS["list"](2), KINDS["list"](3)].index(KINDS["list"](4))), (1, [1, 2]))
assert_eq(run(lambda: [KINDS["list"](1, False), KINDS["list"](2), KINDS["list"](3)].count(KINDS["list"](4))), (2, [1, 2, 3]))
assert_eq(run(lambda: (KINDS["list"](1, False), KINDS["list"](2)).index(KINDS["list"](4))), (1, [1, 2]))
assert_eq(run(lambda: (KINDS["list"](1, False), KINDS["list"](2)).count(KINDS["list"](4))), (1, [1, 2]))
assert_eq(run(lambda: [KINDS["list"](1, False), KINDS["list"](2, False)].index(KINDS["list"](4))), (('ValueError', 'list.index(x): x not in list'), [1, 2]))
assert_eq(run(lambda: [KINDS["list"](1, 'raise'), KINDS["list"](2)].count(KINDS["list"](4))), (('ValueError', '1'), [1]))
assert_eq(run(lambda: [3, KINDS["list"](2)].index(KINDS["list"](4), 1)), (1, [2]))
assert_eq(run(lambda: removed([KINDS["list"](1, False), KINDS["list"](2), KINDS["list"](3)], KINDS["list"](4))), (2, [1, 2]))
assert_eq(run(lambda: [KINDS["list"](1, False), 5, KINDS["list"](2)].index(KINDS["list"](4))), (2, [1, 2]))
assert_eq(run(lambda: [KINDS["list"](1), KINDS["list"](2)].index(KINDS["list"](4), 1, 2)), (1, [2]))
assert_eq(run(lambda: [KINDS["dict"](1, False), KINDS["dict"](2), KINDS["dict"](3)].index(KINDS["dict"](4))), (1, [1, 2]))
assert_eq(run(lambda: [KINDS["dict"](1, False), KINDS["dict"](2), KINDS["dict"](3)].count(KINDS["dict"](4))), (2, [1, 2, 3]))
assert_eq(run(lambda: (KINDS["dict"](1, False), KINDS["dict"](2)).index(KINDS["dict"](4))), (1, [1, 2]))
assert_eq(run(lambda: (KINDS["dict"](1, False), KINDS["dict"](2)).count(KINDS["dict"](4))), (1, [1, 2]))
assert_eq(run(lambda: [KINDS["dict"](1, False), KINDS["dict"](2, False)].index(KINDS["dict"](4))), (('ValueError', 'list.index(x): x not in list'), [1, 2]))
assert_eq(run(lambda: [KINDS["dict"](1, 'raise'), KINDS["dict"](2)].count(KINDS["dict"](4))), (('ValueError', '1'), [1]))
assert_eq(run(lambda: [3, KINDS["dict"](2)].index(KINDS["dict"](4), 1)), (1, [2]))
assert_eq(run(lambda: removed([KINDS["dict"](1, False), KINDS["dict"](2), KINDS["dict"](3)], KINDS["dict"](4))), (2, [1, 2]))
assert_eq(run(lambda: [KINDS["dict"](1, False), 5, KINDS["dict"](2)].index(KINDS["dict"](4))), (2, [1, 2]))
assert_eq(run(lambda: [KINDS["dict"](1), KINDS["dict"](2)].index(KINDS["dict"](4), 1, 2)), (1, [2]))
assert_eq(run(lambda: [((E(1, False),),), ((E(2),),)].index(((E(3),),))), (1, [1, 2]))
assert_eq(run(lambda: [{1: (E(1),), 2: frozendict({3: E(2)})}].count({1: (E(3),), 2: frozendict({3: E(4)})})), (1, [1, 2]))
assert_eq(run(lambda: list(gen())), ([0, 1], [1, 3]))
