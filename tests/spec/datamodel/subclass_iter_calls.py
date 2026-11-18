# spec: PLS-315 7.7.1, 13.2.6
# description: GetIterator calls the Python __iter__ of a builtin's
# subclass that overrides it: a for loop, a comprehension, a generator
# expression's source, yield from and an unpacking over a list, tuple,
# dict, set, frozenset, str, bytes, bytearray or int subclass, and every
# consumer of a dict subclass (set(), frozenset(), list(), the set methods,
# sorted, join, min, max, any, all, zip, enumerate, map, dict.fromkeys and
# a call's starred argument); a generator function as __iter__ is called
# at once, an error it raises propagates, and a result that is not an
# iterator raises TypeError. Membership in a container's subclass is its
# base's (only an int subclass's searches by __iter__), and dict(),
# dict.update() and a ** unpacking of a dict subclass read its keys, not
# __iter__. Inside functions as at module level.
from harness import *

log = []

class DI(dict):
    def __iter__(self):
        for _ in range(2): pass
        log.append("iter")
        return iter(["x", "y"])

class DG(dict):
    def __iter__(self):
        log.append("gen")
        yield "g"

class FI(frozendict):
    def __iter__(self):
        for _ in range(2): pass
        log.append("iter")
        return iter(["f"])

def logged(call):
    del log[:]
    r = call()
    return r, list(log)

def uses():
    d = DI(a=1, x=2)
    calls = [lambda: sorted(set().union(d)), lambda: sorted(set(d)), lambda: sorted(frozenset(d)), lambda: list(d), lambda: tuple(d),
             lambda: sorted({"q", "x"}.symmetric_difference(d)), lambda: {"x"}.issubset(d), lambda: {"x", "y"}.issuperset(d),
             lambda: {"y"}.isdisjoint(d), lambda: sorted({"x", "a"}.intersection(d)), lambda: sorted({"x", "a"}.difference(d)),
             lambda: (lambda s: (s.update(d), sorted(s))[1])(set()), lambda: sorted(d), lambda: "-".join(d), lambda: min(d), lambda: max(d),
             lambda: any(d), lambda: all(d), lambda: list(zip(d, d)), lambda: list(enumerate(d)), lambda: list(map(str.upper, d)),
             lambda: sorted(dict.fromkeys(d)), lambda: [k for k in d], lambda: (lambda a, b: a + b)(*d),
             lambda: "x" in d, lambda: "y" in d, lambda: dict(d), lambda: (lambda e: (e.update(d), e)[1])({}),
             lambda: {**d}, lambda: list(DG()), lambda: sorted(set(DG())), lambda: list(FI(q=1)), lambda: sorted(set(FI(q=1))),
             lambda: dict(FI(q=1))]
    out = [logged(f) for f in calls]
    a, b = d
    out.append((a, b))
    return out


def subclass(base, items):
    class Sub(base):
        def __iter__(self):
            for _ in range(2): pass
            log.append(base.__name__)
            return iter(items)
    return Sub

class GL(list):
    def __iter__(self):
        log.append("gen")
        yield "g"

class Exc(dict):
    def __iter__(self):
        for _ in range(2): pass
        raise ValueError("no")

class Bad(list):
    def __iter__(self): return 5

def loops():
    out = []
    for base, arg in ((list, [1]), (tuple, (1,)), (dict, {1: 2}), (set, {1}), (frozenset, {1}), (str, "s"), (bytes, b"b"), (bytearray, b"b"), (int, 3)):
        sub = subclass(base, ["a", "b"])(arg)
        del log[:]
        got = []
        for x in sub: got.append(x)
        def gen(): yield from sub
        out.append((got, [x for x in sub], list(x for x in sub), sorted({x for x in sub}), list(gen()), log[:]))
    del log[:]
    out.append(([x for x in GL()], log[:]))
    out.append(str(assert_raises(ValueError, lambda: [x for x in Exc()])))
    def loop():
        for x in Bad(): pass
    out.append(str(assert_raises(TypeError, loop)))
    return out

def memberships():
    out = []
    for base, arg in ((list, ["a"]), (tuple, ("a",)), (dict, {"a": 1}), (frozendict, {"a": 1}), (set, {"a"}), (frozenset, {"a"}),
                      (str, "a"), (bytes, b"a"), (bytearray, b"a"), (int, 3)):
        sub = subclass(base, ["z"])(arg)
        del log[:]
        a, z = (b"a", ord("z")) if base in (bytes, bytearray) else ("a", "z")
        out.append((a in sub, z in sub, z not in sub, log[:]))
    return out

found = [(True, False, True, [])] * 9 + [(False, True, False, ["int", "int", "int"])]

used = [(['x', 'y'], ['iter']),
        (['x', 'y'], ['iter']),
        (['x', 'y'], ['iter']),
        (['x', 'y'], ['iter']),
        (('x', 'y'), ['iter']),
        (['q', 'y'], ['iter']),
        (True, ['iter']),
        (True, ['iter']),
        (False, ['iter']),
        (['x'], ['iter']),
        (['a'], ['iter']),
        (['x', 'y'], ['iter']),
        (['x', 'y'], ['iter']),
        ('x-y', ['iter']),
        ('x', ['iter']),
        ('y', ['iter']),
        (True, ['iter']),
        (True, ['iter']),
        ([('x', 'x'), ('y', 'y')], ['iter', 'iter']),
        ([(0, 'x'), (1, 'y')], ['iter']),
        (['X', 'Y'], ['iter']),
        (['x', 'y'], ['iter']),
        (['x', 'y'], ['iter']),
        ('xy', ['iter']),
        (True, []),
        (False, []),
        ({'a': 1, 'x': 2}, []),
        ({'a': 1, 'x': 2}, []),
        ({'a': 1, 'x': 2}, []),
        (['g'], ['gen']),
        (['g'], ['gen']),
        (['f'], ['iter']),
        (['f'], ['iter']),
        ({'q': 1}, []),
        ('x', 'y')]

looped = [(["a", "b"],) * 5 + ([name] * 5,) for name in ("list", "tuple", "dict", "set", "frozenset", "str", "bytes", "bytearray", "int")]
looped += [(['g'], ['gen']), 'no', 'Bad.__iter__() must return an iterator, not int']

def main():
    return uses(), loops(), memberships()

assert_eq(main(), (used, looped, found))
assert_eq((uses(), loops(), memberships()), (used, looped, found))
