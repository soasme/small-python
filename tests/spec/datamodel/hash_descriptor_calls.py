# spec: PLS-315 10.3, 7.5.7, 26, 28
# description: A __hash__ that is a descriptor is read by its Python
# __get__, which may loop, with the key and its class, and what it gives is
# called with no arguments, wherever a key is hashed: hash(), a set or
# dict display, a lookup, a store, set.add and a tuple holding the key.
# An AttributeError from __get__ makes the key unhashable; any other
# exception propagates. The same holds for a __get__ that does not loop.
from harness import *

log = []
def spin():
    for _ in range(2): pass
class Hashing:
    def __get__(self, obj, owner):
        spin(); log.append(("get", owner.__name__))
        if getattr(obj, "fail", None) == "attr": raise AttributeError("gone")
        if getattr(obj, "fail", None) == "key": raise KeyError("get")
        return lambda: obj.value
class Key:
    __hash__ = Hashing()
    def __init__(self, value, fail=None): self.value, self.fail = value, fail
    def __eq__(self, other): return isinstance(other, Key) and self.value == other.value

def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
one = [("get", "Key")]
def cases():
    k = Key(5)
    d = {}
    def store(): d[k] = 1; return d[Key(5)]
    def add(): s = set(); s.add(k); return len(s)
    return [run(lambda: hash(k)), run(lambda: len({k})), run(lambda: k in {5: 0}), run(store), run(add),
            run(lambda: hash((k, 1)) == hash((5, 1))), run(lambda: {(k,): 2}[(Key(5),)]),
            run(lambda: hash(Key(1, "attr"))), run(lambda: {Key(1, "attr")}), run(lambda: (Key(1, "attr"),) in {}),
            run(lambda: hash(Key(1, "key")))]
expected = [(5, one), (1, one), (False, one), (1, one * 2), (1, one), (True, one), (2, one * 2),
            (("TypeError", "unhashable type: 'Key'"), one), (("TypeError", "cannot use 'Key' as a set element (unhashable type: 'Key')"), one),
            (("TypeError", "cannot use 'tuple' as a dict key (unhashable type: 'Key')"), one), (("KeyError", "'get'"), one)]
assert_eq(cases(), expected)
assert_eq(cases(), expected)

class Plain:
    def __get__(self, obj, owner): raise AttributeError("gone")
class Bare:
    __hash__ = Plain()
assert_eq([run(lambda: hash(Bare()))[0], run(lambda: {Bare()})[0], run(lambda: frozenset([Bare()]))[0]],
          [("TypeError", "unhashable type: 'Bare'"), ("TypeError", "cannot use 'Bare' as a set element (unhashable type: 'Bare')"),
           ("TypeError", "cannot use 'Bare' as a set element (unhashable type: 'Bare')")])
