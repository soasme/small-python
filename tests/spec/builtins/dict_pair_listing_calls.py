# spec: PLS-315 26.1.1 26.1.3 7.7.8
# description: dict() and dict.update() of an iterable of pairs take each
# element that is no list or tuple by SequenceFast: its iterator, then a
# list of what that iterator gives, which asks the iterator's own
# __iter__ and length hint again; a generator's items are listed as it
# runs. A pair whose key has a Python __hash__ is hashed after it is
# listed. A TypeError listing an element gets a note naming its index,
# another error propagates as it is, and an element listing to a length
# other than 2 raises ValueError; keywords merge after the pairs.
from harness import *

log = []
def pair(k, v):
    log.append(("gen", k))
    yield k
    yield v

class Own:
    def __init__(self, *items): self.items = list(items)
    def __iter__(self):
        for _ in (): pass
        log.append("iter")
        return self
    def __next__(self):
        if not self.items: raise StopIteration
        return self.items.pop(0)
    def __len__(self):
        log.append("len")
        return len(self.items)

class Key:
    def __init__(self, v): self.v = v
    def __hash__(self):
        for _ in (): pass
        log.append(("hash", self.v))
        return hash(self.v)
    def __eq__(self, other): return isinstance(other, Key) and self.v == other.v
    def __repr__(self): return "Key(%r)" % (self.v,)

def failing(error):
    yield "k"
    raise error

def attempt(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e), getattr(e, "__notes__", None))

def results():
    for _ in (): pass
    del log[:]
    d = {"z": 0}
    d.update([pair("u", 1)], w=2)
    out = [dict([pair("a", 1), ("b", 2), pair("c", 3)]),
           dict([Own("o", 4)]),
           dict(pair(k, i) for i, k in enumerate("xy")),
           d,
           dict([pair(Key(1), "k")]),
           attempt(lambda: dict([("a", 1), failing(TypeError("t"))])),
           attempt(lambda: dict([failing(KeyError("e"))])),
           attempt(lambda: dict([pair("a", 1), Own(1, 2, 3)])),
           dict([pair("a", 1)], a=5)]
    return out, list(log)

expected = ([{"a": 1, "b": 2, "c": 3}, {"o": 4}, {"x": 0, "y": 1}, {"z": 0, "u": 1, "w": 2}, {Key(1): "k"},
             ("TypeError", "t", ["Cannot convert dictionary update sequence element #1 to a sequence"]),
             ("KeyError", "'e'", None),
             ("ValueError", "dictionary update sequence element #1 has length 3; 2 is required", None),
             {"a": 5}],
            [("gen", "u"), ("gen", "a"), ("gen", "c"), "iter", "iter", "len", ("gen", "x"), ("gen", "y"),
             ("gen", Key(1)), ("hash", 1), ("gen", "a"), "iter", "iter", "len", ("gen", "a")])

assert_eq(results(), expected)
assert_eq(results(), expected)
