# spec: PLS-315 13.3.4, 13.2.3
# description: A call's ** of a mapping calls its Python keys once, then
# for each key, in order, finds whether the call already has it, raising
# the duplicate keyword's TypeError before reading the value, else reads
# it by the Python __getitem__ and merges it; keys and __getitem__ may
# loop. Before and after keyword arguments, starred arguments and other
# ** mappings, a generator keys() too, inside functions as at module
# level.
from harness import *

log = []

def spin():
    for _ in (): pass

class M:
    def __init__(self, *ks): self.ks = ks
    def keys(self):
        spin()
        log.append("keys")
        return list(self.ks)
    def __getitem__(self, k):
        spin()
        log.append("get " + k)
        return k.upper()

class Gen(M):
    def keys(self):
        log.append("gen")
        yield from self.ks

def f(*a, **k): return a, k

def error(g):
    try:
        return g()
    except TypeError as e:
        return str(e)

def results():
    del log[:]
    out = [f(**M("a", "b")), f(0, x=1, **M("c")), f(*[1], **M("d"), y=2), f(**M("e"), **Gen("g", "h")), list(log)]
    del log[:]
    out += [error(lambda: f(a=1, **M("b", "a", "c"))), error(lambda: f(**M("a", "a"))), error(lambda: f(**M("a"), **M("b", "a"))), list(log)]
    return out

expected = [((), {"a": "A", "b": "B"}), ((0,), {"x": 1, "c": "C"}), ((1,), {"d": "D", "y": 2}),
            ((), {"e": "E", "g": "G", "h": "H"}),
            ["keys", "get a", "get b", "keys", "get c", "keys", "get d", "keys", "get e", "gen", "get g", "get h"],
            "__main__.f() got multiple values for keyword argument 'a'", "__main__.f() got multiple values for keyword argument 'a'",
            "__main__.f() got multiple values for keyword argument 'a'",
            ["keys", "get b", "keys", "get a", "keys", "get a", "keys", "get b"]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
