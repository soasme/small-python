# spec: PLS-315 13.2.3, 13.3.4, 26.5
# description: DictMerge lists all of a mapping's keys, iterating what its
# keys() returns to the end, before it looks up the first of them, for a
# ** display item, a ** call argument, dict(), dict.update() and
# frozendict(); a list keys() returns is iterated as it is, so keys its
# __getitem__ appends are merged too, and an exception while listing the
# keys raises before any lookup. An exception from keys() or __getitem__
# propagates, a keys() result that is not iterable raises TypeError naming
# the method, qualified by the class's module unless that is builtins or
# __main__, dict.update() returns None, and a keys attribute of the
# instance itself is the one called.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Lazy:
    def keys(self):
        for k in "ab":
            log.append(("key", k))
            yield k
    def __getitem__(self, k):
        spin()
        log.append(("get", k))
        return k.upper()

class Listed(Lazy):
    def keys(self):
        spin()
        return ["p", "q"]

class Missing(Listed):
    def __getitem__(self, k):
        spin()
        raise KeyError(k)

class Raising(Lazy):
    def keys(self):
        spin()
        raise ValueError("keys")

class Unlisted(Lazy):
    def keys(self):
        spin()
        return 5

class Elsewhere(Unlisted):
    __module__ = "elsewhere"

class Growing:
    def __init__(self): self.names = ["x"]
    def keys(self): return self.names
    def __getitem__(self, k):
        log.append(("get", k))
        if len(self.names) < 3: self.names.append(k * 2)
        return len(k)

class Failing:
    def keys(self):
        yield "a"
        raise KeyError("listing")
    def __getitem__(self, k):
        log.append(("get", k))
        return 0

def keywords(**kw):
    return kw

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    d = {}
    out = [d.update(Lazy())]
    out += [dict(Lazy()), d, {**Lazy()}, keywords(**Lazy()), frozendict(Lazy()), dict(Growing()),
            error(lambda: dict(Failing())), error(lambda: {**Failing()})]
    own = Listed()
    own.keys = lambda: ["o"]
    out += [dict(Listed()), dict(own), error(lambda: dict(Missing())), error(lambda: {}.update(Raising())),
            error(lambda: dict(Unlisted())), error(lambda: {}.update(Elsewhere()))]
    out.append(list(log))
    return out

lazy = [("key", "a"), ("key", "b"), ("get", "a"), ("get", "b")]
upper = {"a": "A", "b": "B"}
expected = [None, upper, upper, upper, upper, frozendict(upper), {"x": 1, "xx": 2, "xxxx": 4},
            ("KeyError", "'listing'"), ("KeyError", "'listing'"), {"p": "P", "q": "Q"}, {"o": "O"}, ("KeyError", "'p'"),
            ("ValueError", "keys"), ("TypeError", "Unlisted.keys() must return an iterable, not int"),
            ("TypeError", "elsewhere.Elsewhere.keys() must return an iterable, not int"),
            lazy * 5 + [("get", "x"), ("get", "xx"), ("get", "xxxx"), ("get", "p"), ("get", "q"), ("get", "o")]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
