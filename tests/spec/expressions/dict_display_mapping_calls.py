# spec: PLS-315 13.2.6, 7.7.4
# description: a dict display's ** item that is an instance with a Python
# keys() and __getitem__ calls keys() once, listing its keys, then
# __getitem__ for each key in order, after the display's earlier items and
# before its later ones, which replace earlier values; keys() may be a
# generator function, and keys with a Python __hash__ and __eq__ are
# merged as any key; an error from either method propagates from the
# display; inside nested displays and functions as at module level.
from harness import *

log = []

class Mapping:
    def __init__(self, keys): self._keys = keys
    def keys(self):
        log.append("keys")
        return list(self._keys)
    def __getitem__(self, key):
        log.append(("get", key))
        return str(key) * 2

class Lazy:
    def keys(self):
        log.append("keys")
        yield "x"
        log.append("more")
        yield "y"
    def __getitem__(self, key):
        log.append(("get", key))
        return key.upper()

class Key:
    def __init__(self, name): self.name = name
    def __hash__(self):
        log.append(("hash", self.name))
        return 7
    def __eq__(self, other):
        log.append(("eq", self.name))
        return isinstance(other, Key) and other.name == self.name
    def __repr__(self): return self.name

def note(x):
    log.append(("item", x))
    return x

def merges():
    out = [{note("a"): 0, **Mapping("ab"), "b": 1}]
    out.append(log[:]); log.clear()
    out.append([{**Lazy()}, ({**Mapping("c")}, 2)])
    out.append(log[:]); log.clear()
    k = Key("k")
    d = {k: 0, **Mapping([Key("k")])}
    out.append((list(d.values()), log[:])); log.clear()
    return out

expected = [
    {"a": "aa", "b": 1},
    [("item", "a"), "keys", ("get", "a"), ("get", "b")],
    [{"x": "X", "y": "Y"}, ({"c": "cc"}, 2)],
    ["keys", "more", ("get", "x"), ("get", "y"), "keys", ("get", "c")],
    (["kk"], [("hash", "k"), "keys", ("get", Key("k")), ("hash", "k"), ("eq", "k")]),
]
result = merges()
assert_eq(result[:4], expected[:4])
# Key's repr is its name.
assert_eq(repr(result[4]), repr(expected[4]))
log.clear()
assert_eq({**Mapping("z")}, {"z": "zz"})
assert_eq(log, ["keys", ("get", "z")])
log.clear()

# An error from keys() or __getitem__ propagates from the display.
class BadKeys(Mapping):
    def keys(self): raise KeyError("keys")
class BadItem(Mapping):
    def __getitem__(self, key):
        if key == "b": raise LookupError(key)
        return 0

def errors():
    out = []
    try: {**BadKeys("a")}
    except KeyError as e: out.append(e.args)
    try: [{"z": 1, **BadItem("ab")}]
    except LookupError as e: out.append(e.args)
    return out

assert_eq(errors(), [("keys",), ("b",)])
