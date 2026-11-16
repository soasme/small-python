# spec: PLS-315 13.2.3, 13.3.4, 26.1.1
# description: When a mapping's keys() returns an object whose class
# defines __iter__, a display's **, a call's ** and dict(), dict.update()
# list the keys by that Python __iter__, which may loop or be a
# generator function, before looking up the first by __getitem__; an
# exception of __iter__ propagates before any lookup, and a call's
# duplicate key raises TypeError. Inside functions as at module level.
from harness import *

log = []

class Keys:
    def __init__(self, ks, bad=False): self.ks, self.bad = ks, bad
    def __iter__(self):
        for _ in range(2): pass
        log.append("iter")
        if self.bad: raise LookupError("iter")
        return iter(self.ks)

class Generated:
    def __iter__(self):
        log.append("gen")
        yield "g"

class Map:
    def __init__(self, keys): self.k = keys
    def keys(self):
        log.append("keys")
        return self.k
    def __getitem__(self, k):
        log.append(("get", k))
        return k * 2

def f(**kw): return kw

def update(m):
    d = {}
    d.update(m)
    return d

def t(call):
    try:
        r = call()
    except Exception as e:
        r = type(e).__name__ + ": " + str(e)
    out = (r, log[:])
    del log[:]
    return out

def results():
    return [t(lambda: {**Map(Keys(["a", "b"]))}), t(lambda: f(**Map(Keys(["c"])))), t(lambda: dict(Map(Keys(["d"])))),
            t(lambda: update(Map(Keys(["e"])))), t(lambda: dict(Map(Generated()))), t(lambda: {**Map(Keys([], True))}),
            t(lambda: f(**Map(Keys(["x", "x"])))), t(lambda: {"z": 0, **Map(Keys(["z"]))})]

expected = [({'a': 'aa', 'b': 'bb'}, ['keys', 'iter', ('get', 'a'), ('get', 'b')]),
            ({'c': 'cc'}, ['keys', 'iter', ('get', 'c')]), ({'d': 'dd'}, ['keys', 'iter', ('get', 'd')]),
            ({'e': 'ee'}, ['keys', 'iter', ('get', 'e')]), ({'g': 'gg'}, ['keys', 'gen', ('get', 'g')]),
            ('LookupError: iter', ['keys', 'iter']),
            ("TypeError: __main__.f() got multiple values for keyword argument 'x'", ['keys', 'iter', ('get', 'x')]),
            ({'z': 'zz'}, ['keys', 'iter', ('get', 'z')])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
