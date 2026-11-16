# spec: PLS-315 26.2, 26.1.1
# description: frozendict() of an object with keys merges it as dict()
# does, by its Python keys() and __getitem__, which may loop, in that
# order; of a generator it takes the pairs it yields; keywords merge after
# the source's items; an exception from keys(), __getitem__ or the
# generator propagates, and an item that is no pair raises TypeError.
# Inside functions as at module level.
from harness import *

log = []

class Mapping:
    def __init__(self, bad=None): self.bad = bad
    def keys(self):
        for _ in range(2): pass
        log.append("keys")
        if self.bad == "keys": raise LookupError("keys")
        return ["a", "b"]
    def __getitem__(self, key):
        for _ in range(2): pass
        log.append(key)
        if self.bad == key: raise LookupError(key)
        return key.upper()

def pairs(bad=None):
    log.append("gen")
    yield ("x", 1)
    if bad: raise LookupError("gen")
    yield ("y", 2)

def t(f):
    try:
        r = f()
        r = (type(r).__name__, dict(r))
    except Exception as e:
        r = type(e).__name__ + ": " + str(e)
    out = (r, log[:])
    del log[:]
    return out

def results():
    return [t(lambda: frozendict(Mapping())), t(lambda: frozendict(pairs())), t(lambda: frozendict(Mapping(), a=0, c=3)),
            t(lambda: frozendict(pairs(), x=9)), t(lambda: frozendict(Mapping("keys"))), t(lambda: frozendict(Mapping("b"))),
            t(lambda: frozendict(pairs(True))), t(lambda: frozendict(x for x in [1])),
            t(lambda: frozendict(h=hash(frozendict(Mapping())) == hash(frozendict(a="A", b="B"))))]

expected = [(('frozendict', {'a': 'A', 'b': 'B'}), ['keys', 'a', 'b']), (('frozendict', {'x': 1, 'y': 2}), ['gen']),
            (('frozendict', {'a': 0, 'b': 'B', 'c': 3}), ['keys', 'a', 'b']),
            (('frozendict', {'x': 9, 'y': 2}), ['gen']), ('LookupError: keys', ['keys']),
            ('LookupError: b', ['keys', 'a', 'b']), ('LookupError: gen', ['gen']),
            ('TypeError: object is not iterable', []), (('frozendict', {'h': True}), ['keys', 'a', 'b'])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
