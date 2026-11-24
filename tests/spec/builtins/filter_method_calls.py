# spec: PLS-315 27.1.5, 27.1.6
# description: filter() of a bound method calls it once per item as the
# filter reaches it: a Python method, a slot wrapper bound to an instance
# whose class's Python __missing__ or __eq__ it reaches, or a property's
# __get__ running the getter; map() of a property's __get__, __set__ or
# __delete__ runs the accessor once per item. Errors propagate. In a list,
# a comprehension, yield from and next().
from harness import *

log = []

class P:
    def __init__(self, v): self.v = v
    @property
    def x(self):
        for _ in (): pass
        log.append(("get", self.v))
        if self.v < 0: raise LookupError("get")
        return self.v
    @x.setter
    def x(self, value):
        for _ in (): pass
        log.append(("set", value))
    @x.deleter
    def x(self):
        for _ in (): pass
        log.append(("del", self.v))
    def odd(self, n):
        for _ in (): pass
        log.append(("odd", n))
        return n % 2

class D(dict):
    def __missing__(self, key):
        for _ in (): pass
        log.append(("missing", key))
        return key > 1

class E:
    def __eq__(self, other):
        for _ in (): pass
        log.append(("eq", other))
        return other == 2

def run():
    out = [[p.v for p in filter(P.x.__get__, [P(1), P(0)])]]
    out.append([n for n in filter(P(0).odd, [1, 2, 3])])
    out.append(list(filter(D({0: True}).__getitem__, [0, 1, 2])))
    def gen():
        yield from filter(E().__eq__, [1, 2])
    out.append(list(gen()))
    f = filter(D().__getitem__, [1, 5])
    out.append(next(f))
    out.append(list(map(P.x.__get__, [P(7)])))
    out.append(list(map(P.x.__set__, [P(0)], [8])))
    out.append(list(map(P.x.__delete__, [P(9)])))
    return out

assert_eq(run(), [[1], [1, 3], [0, 2], [2], 5, [7], [None], [None]])
assert_eq(log, [("get", 1), ("get", 0), ("odd", 1), ("odd", 2), ("odd", 3), ("missing", 1), ("missing", 2),
                ("eq", 1), ("eq", 2), ("missing", 1), ("missing", 5), ("get", 7), ("set", 8), ("del", 9)])
del log[:]
assert_raises(LookupError, list, filter(P.x.__get__, [P(1), P(-1)]))
assert_raises(LookupError, list, map(P.x.__get__, [P(-2)]))
assert_eq(log, [("get", 1), ("get", -1), ("get", -2)])
