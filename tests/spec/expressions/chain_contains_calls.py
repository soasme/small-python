# spec: PLS-315 13.10
# description: An in or not in inside a comparison chain searches its
# right operand as a lone one does, item by item through Python __eq__,
# __iter__, __getitem__ or a generator, then goes on with that same
# operand as the next comparison's left one when true, and stops the
# chain with False otherwise, evaluating nothing further; an error in the
# search propagates.
from harness import *

log = []

class E:
    def __init__(self, v): self.v = v
    def __eq__(self, other):
        for _ in (): pass
        log.append(("eq", self.v))
        return self.v == other
    __hash__ = None

class P:
    def __init__(self, v): self.v = v
    def __eq__(self, other):
        log.append(("peq", self.v))
        return self.v == other
    __hash__ = None

class It:
    def __iter__(self):
        for _ in (): pass
        log.append("iter")
        return iter([1, 2])

class Gen:
    def __iter__(self):
        log.append("gen")
        yield 1
        yield 2

class Item:
    def __getitem__(self, i):
        log.append(("item", i))
        return [1, 2][i]

def booh(self): raise AttributeError("booh")
Absent = type("Absent", (), {"__contains__": property(booh), "__iter__": It.__iter__})

class Bad:
    def __iter__(self): raise KeyError("bad")

class Y:
    def __init__(self, items): self.items = items
    def __iter__(self): return iter(self.items)
    def __eq__(self, other):
        log.append(("Y", other))
        return "same"
    __hash__ = None

def side(v):
    log.append(("side", v))
    return v

def attempt(f):
    try: return f()
    except KeyError as e: return ("KeyError", str(e))

def results():
    for _ in (): pass
    del log[:]
    items = [E(5), E(1)]
    pairs = [(P(5), 0), (P(1), 0)]
    y = Y([2])
    out = [
        0 < 1 in items is items,
        0 < 3 in items is side(items),
        1 in tuple(items) is not side(None),
        1 not in items is items,
        (1, 0) in pairs is pairs,
        1 in iter(items) is not None,
        0 < 2 in It() is not side(None),
        0 < 3 in It() is not side(None),
        2 in Gen() is not None,
        1 in (v for v in items) is not side(None),
        7 in (v for v in items) is not side(None),
        2 in Item() is not None,
        2 in Absent() is not None,
        2 in y == 7,
        3 in y == 7,
        attempt(lambda: 0 < 1 in Bad() is not side(None)),
        list(log),
    ]
    return out

expected = [
    True, False, True, False, True, True, True, False, True, True, False, True, True, "same", False,
    ("KeyError", "'bad'"),
    [("eq", 5), ("eq", 1),
     ("eq", 5), ("eq", 1),
     ("eq", 5), ("eq", 1), ("side", None),
     ("eq", 5), ("eq", 1),
     ("peq", 5), ("peq", 1),
     ("eq", 5), ("eq", 1),
     "iter", ("side", None),
     "iter",
     "gen",
     ("eq", 5), ("eq", 1), ("side", None),
     ("eq", 5), ("eq", 1),
     ("item", 0), ("item", 1),
     "iter",
     ("Y", 7)],
]

assert_eq(results(), expected)
assert_eq(results(), expected)
