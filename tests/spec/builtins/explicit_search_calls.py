# spec: PLS-315 25.5.2, 25.5.3, 13.10
# description: A container's __contains__ and rich comparison methods
# called explicitly, bound or given the container, and index(), count()
# and remove() called with unpacked arguments, compare each item with a
# Python __eq__ in order as `in`, ==, < and the plain calls do, its
# exception propagating; an instance of an int subclass is searched too.
from harness import *

log = []
class E:
    def __init__(self, v): self.v = v
    def __eq__(self, other):
        for _ in (): pass
        log.append(("eq", self.v, other))
        if other == "boom": raise KeyError("k")
        return other == self.v
    def __lt__(self, other):
        log.append(("lt", self.v, other))
        return True
    __hash__ = None
class I(int):
    def __eq__(self, other):
        log.append(("I", int(self), other))
        return isinstance(other, int) and int(self) % 10 == other % 10
    __hash__ = int.__hash__
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, list(log)

# Explicit special methods.
assert_eq(run(lambda: [0, 1, 2].__contains__(E(1))), (True, [("eq", 1, 0), ("eq", 1, 1)]))
assert_eq(run(lambda: list.__contains__([2], E(2))), (True, [("eq", 2, 2)]))
assert_eq(run(lambda: (0, 2).__contains__(E(5))), (False, [("eq", 5, 0), ("eq", 5, 2)]))
assert_eq(run(lambda: ["boom"].__contains__(E(1))), (("KeyError", "'k'"), [("eq", 1, "boom")]))
assert_eq(run(lambda: range(4).__contains__(E(2))), (True, [("eq", 2, 0), ("eq", 2, 1), ("eq", 2, 2)]))
contains = [7, 8].__contains__
assert_eq(run(lambda: contains(E(8))), (True, [("eq", 8, 7), ("eq", 8, 8)]))
assert_eq(run(lambda: [E(1)].__eq__([2])), (False, [("eq", 1, 2)]))
assert_eq(run(lambda: [E(2)].__ne__([2])), (False, [("eq", 2, 2)]))
assert_eq(run(lambda: (E(1),).__lt__((2,))), (True, [("eq", 1, 2), ("lt", 1, 2)]))
assert_eq(run(lambda: [E(1)].__eq__(["boom"])), (("KeyError", "'k'"), [("eq", 1, "boom")]))
assert_eq(run(lambda: [1].__lt__("x")), (NotImplemented, []))
assert_eq(run(lambda: [].__contains__()), (("TypeError", "expected 1 argument, got 0"), []))

# Searches given unpacked arguments.
r, l, t = range(5), [1, 2, 3, 2], (1, 2, 3, 2)
assert_eq(run(lambda: r.index(*(E(3),))), (3, [("eq", 3, 0), ("eq", 3, 1), ("eq", 3, 2), ("eq", 3, 3)]))
assert_eq(run(lambda: r.count(*(E(4),))), (1, [("eq", 4, 0), ("eq", 4, 1), ("eq", 4, 2), ("eq", 4, 3), ("eq", 4, 4)]))
assert_eq(run(lambda: l.index(*(E(2), 2))), (3, [("eq", 2, 3), ("eq", 2, 2)]))
assert_eq(run(lambda: t.count(*(E(2),))), (2, [("eq", 2, 1), ("eq", 2, 2), ("eq", 2, 3), ("eq", 2, 2)]))
assert_eq(run(lambda: list.index(*(l, E(9)))), (("ValueError", "list.index(x): x not in list"), [("eq", 9, 1), ("eq", 9, 2), ("eq", 9, 3), ("eq", 9, 2)]))
m = [5, 6]
assert_eq(run(lambda: (m.remove(*(E(6),)), m)), ((None, [5]), [("eq", 6, 5), ("eq", 6, 6)]))
assert_eq(run(lambda: l.index(*())), (("TypeError", "index expected at least 1 argument, got 0"), []))
assert_eq(run(lambda: list.index(*())), (("TypeError", "unbound method list.index() needs an argument"), []))

# An int subclass's instance is compared as any item is.
assert_eq(run(lambda: (I(11) in [3, 1], I(11) in (21,), [3, 1].count(I(11)))),
          ((True, True, 1), [("I", 11, 3), ("I", 11, 1), ("I", 11, 21), ("I", 11, 3), ("I", 11, 1)]))

def inside():
    return [l.index(*(E(3),)) for _ in range(2)], (E(1),).__eq__((1,))
assert_eq(run(inside), (([2, 2], True), [("eq", 3, 1), ("eq", 3, 2), ("eq", 3, 3), ("eq", 3, 1), ("eq", 3, 2), ("eq", 3, 3), ("eq", 1, 1)]))
def made():
    yield [E(5)].__contains__(5)
    yield t.count(*(E(3),))
assert_eq(run(lambda: list(made())), ([True, 1], [("eq", 5, 5), ("eq", 3, 1), ("eq", 3, 2), ("eq", 3, 3), ("eq", 3, 2)]))
