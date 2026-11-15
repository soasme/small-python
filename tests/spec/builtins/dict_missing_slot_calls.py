# spec: PLS-315 26.1.2, 7.3.2
# description: dict.__getitem__ called on an instance of a dict subclass,
# unbound, bound, or through super() in the class's own __getitem__,
# returns a present key's value and calls the class's __missing__, which
# may loop, with an absent key, its result the call's value and its
# exception raised there. A key with a Python __eq__, a staticmethod
# __missing__ and a wrong arity behave alike. Inside functions as at
# module level. A dict method found on the instance, special or not, has
# the instance as its __self__.
from harness import *

log = []

class Counts(dict):
    def __missing__(self, key):
        for _ in range(2): pass
        log.append(("missing", key))
        if key == "bad":
            raise LookupError("no " + key)
        return len(log)

class Over(Counts):
    def __getitem__(self, key):
        for _ in range(2): pass
        log.append(("getitem", key))
        return super().__getitem__(key) * 10

class Static(dict):
    @staticmethod
    def __missing__(key):
        log.append(("static", key))
        return key * 2

class Narrow(dict):
    def __missing__(self): pass

class Key:
    def __init__(self, n): self.n = n
    def __hash__(self): return hash(self.n)
    def __eq__(self, other):
        log.append(("eq", self.n))
        return isinstance(other, Key) and other.n == self.n

def error(f, *args):
    try:
        f(*args)
    except Exception as e:
        return type(e).__name__, str(e)

def calls():
    del log[:]
    d = Counts(a=1)
    out = [dict.__getitem__(d, "a"), dict.__getitem__(d, "b"), d.__getitem__("c"), d.__getitem__((1, 2))]
    out += [Over(x=2)["x"], Over()["y"], error(dict.__getitem__, d, "bad"), error(d.__getitem__, "bad")]
    out += [dict.__getitem__(Static(), 4), error(dict.__getitem__, Narrow(), 1)]
    k = Counts({Key(1): "one"})
    out += [dict.__getitem__(k, Key(1)), dict.__getitem__(k, 5), d.get("zz"), "zz" in d]
    out.append(list(log))
    return out

expected = [1, 1, 2, 3, 20, 60, ("LookupError", "no bad"), ("LookupError", "no bad"), 8,
            ("TypeError", "Narrow.__missing__() takes 1 positional argument but 2 were given"), "one", 11, None, False,
            [("missing", "b"), ("missing", "c"), ("missing", (1, 2)), ("getitem", "x"), ("getitem", "y"), ("missing", "y"),
             ("missing", "bad"), ("missing", "bad"), ("static", 4), ("eq", 1), ("missing", 5)]]

def main():
    return calls()

assert_eq(main(), expected)
assert_eq(calls(), expected)

d = Counts()
assert_eq([getattr(d, name).__self__ is d for name in ("__getitem__", "__contains__", "__len__", "__setitem__", "__or__", "keys")],
          [True] * 6)
