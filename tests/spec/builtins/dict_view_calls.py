# spec: PLS-315 26.4, 26.6, 7.2.4, 7.3
# description: a dict keys or items view's in, its __contains__, and its
# comparisons with another view or a set look keys up by their Python
# __hash__ and __eq__ and compare an item's value by its __eq__, in
# CPython's order: a comparison walks the left view (the right for > and
# >=) testing each member in the other, a set on the left by the view's
# reflected comparison. An items view takes a tuple subclass's pair; a
# keys or items view's comparison and set methods take a set or view,
# and any iterable. Inside functions and generators as at module level.
from harness import *

log = []
class K:
    def __init__(self, v): self.v = v
    def __hash__(self):
        for _ in (): pass
        log.append(("hash", self.v))
        return self.v
    def __eq__(self, o):
        for _ in (): pass
        log.append(("eq", self.v, getattr(o, "v", o)))
        return isinstance(o, K) and self.v == o.v
    def __repr__(self): return "K(%d)" % self.v

class T(tuple): pass
a, b, x = K(1), K(2), K(10)
d = {a: x, b: K(20)}
e = {K(1): 0, K(2): 0, K(3): 0}

def run(f):
    del log[:]
    try: r = f()
    except TypeError as exc: r = "TypeError"
    return r, list(log)

def cases():
    return [run(lambda: K(1) in d.keys()),
            run(lambda: K(3) not in d.keys()),
            run(lambda: d.keys().__contains__(K(2))),
            run(lambda: (K(1), K(10)) in d.items()),
            run(lambda: (a, x) in d.items()),
            run(lambda: (K(2), K(21)) in d.items()),
            run(lambda: d.items().__contains__((K(2), K(20)))),
            run(lambda: (K(5), 1) in d.items()),
            run(lambda: 1 in d.items()),
            run(lambda: d.keys() == e.keys()),
            run(lambda: d.keys() <= e.keys()),
            run(lambda: e.keys() > d.keys()),
            run(lambda: d.keys() != {K(1), K(2)}),
            run(lambda: d.keys().__eq__(e.keys())),
            run(lambda: d.items() <= e.items()),
            run(lambda: d.items() == dict(d).items()),
            run(lambda: {K(1), K(2)} == d.keys()),
            run(lambda: {K(1)} < d.keys()),
            run(lambda: T((K(1), K(10))) in d.items()),
            run(lambda: d.items().__contains__(T((a, x)))),
            run(lambda: d.keys().__lt__({K(1), K(2), K(5)})),
            run(lambda: d.items().__ge__(dict(d).items())),
            run(lambda: d.keys().__eq__([a, b])),
            run(lambda: d.__contains__(K(2)))]

expected = [(True, [('hash', 1), ('eq', 1, 1)]),
            (True, [('hash', 3)]),
            (True, [('hash', 2), ('eq', 2, 2)]),
            (True, [('hash', 1), ('eq', 1, 1), ('eq', 10, 10)]),
            (True, [('hash', 1)]),
            (False, [('hash', 2), ('eq', 2, 2), ('eq', 20, 21)]),
            (True, [('hash', 2), ('eq', 2, 2), ('eq', 20, 20)]),
            (False, [('hash', 5)]),
            (False, []),
            (False, []),
            (True, [('hash', 1), ('eq', 1, 1), ('hash', 2), ('eq', 2, 2)]),
            (True, [('hash', 1), ('eq', 1, 1), ('hash', 2), ('eq', 2, 2)]),
            (False, [('hash', 1), ('hash', 2), ('hash', 1), ('eq', 1, 1), ('hash', 2), ('eq', 2, 2)]),
            (False, []),
            (False, [('hash', 1), ('eq', 1, 1), ('eq', 10, 0)]),
            (True, [('hash', 1), ('hash', 2)]),
            (True, [('hash', 1), ('hash', 2), ('hash', 1), ('eq', 1, 1), ('hash', 2), ('eq', 2, 2)]),
            (True, [('hash', 1), ('hash', 1), ('eq', 1, 1)]),
            (True, [('hash', 1), ('eq', 1, 1), ('eq', 10, 10)]),
            (True, [('hash', 1)]),
            (True, [('hash', 1), ('hash', 2), ('hash', 5), ('hash', 1), ('eq', 1, 1), ('hash', 2), ('eq', 2, 2)]),
            (True, [('hash', 1), ('hash', 2)]),
            (NotImplemented, []),
            (True, [('hash', 2), ('eq', 2, 2)])]
assert_eq(cases(), expected)

k = {1: 2, 3: 4}.keys()
assert_eq((sorted(k.__sub__([1])), sorted(k.__rsub__({1, 9})), sorted(k.__and__((3,))), sorted(k.__ror__([5])),
           sorted(k.__xor__({1, 7})), sorted({1: 2}.items().__or__([(3, 4)]))), ([3], [9], [3], [1, 3, 5], [3, 7], [(1, 2), (3, 4)]))
assert_raises(TypeError, k.__sub__, 5)
assert_raises(TypeError, k.__rand__, None)
assert_eq((k.__eq__(5), k.__ne__([1, 3]), k.__eq__({1, 3}), k.__le__({1: 0, 3: 0}.keys())), (NotImplemented, NotImplemented, True, True))

def gen():
    yield cases()
assert_eq(next(gen()), expected)

# A stored key's __eq__ declining leaves the probe's reflected Python
# __eq__, and both declining, identity: False.
reflect_log = []
class DeclinedStore:
    def __hash__(self): return 1
    def __eq__(self, other): reflect_log.append("stored"); return NotImplemented
class ReflectedProbe:
    def __hash__(self): return 1
    def __eq__(self, other): reflect_log.append("probe"); return True
class DeclinedProbe:
    def __hash__(self): return 1
    def __eq__(self, other): reflect_log.append("declines"); return NotImplemented
reflect_dict = {DeclinedStore(): "found"}
reflect_found = [ReflectedProbe() in reflect_dict.keys(), (ReflectedProbe(), "found") in reflect_dict.items(),
                 reflect_dict.__contains__(ReflectedProbe()), DeclinedProbe() in reflect_dict.keys()]
assert_eq((reflect_found, reflect_log), ([True, True, True, False], ["stored", "probe"] * 3 + ["stored", "declines"]))
