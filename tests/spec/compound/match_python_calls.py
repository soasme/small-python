# spec: PLS-315 15.6.1, 15.6.2, 15.6.3, 15.6.4, 15.6.5
# description: a match statement's patterns call Python methods of the
# subject and of the patterns' values, which may loop, each once and in
# order: a value pattern's __eq__ (the subject's first), a list
# subclass's __len__ (its items read without __getitem__), a dict
# subclass's get, a metaclass's __instancecheck__ and
# a property read by a class pattern. A failing case's calls happen before
# the next case's; an exception from one propagates out of the match and
# no binding of its case is stored. Inside functions as at module level.
from harness import *

log = []

class P:
    def __init__(self, x): self.x = x
    def __eq__(self, o):
        for _ in (): pass
        log.append(("eq", self.x))
        return isinstance(o, P) and o.x == self.x

class Seq(list):
    def __len__(self):
        for _ in (): pass
        log.append("len")
        return list.__len__(self)
    def __getitem__(self, i):
        for _ in (): pass
        log.append(("item", i))
        return list.__getitem__(self, i)

class Map(dict):
    def get(self, k, d=None):
        for _ in (): pass
        log.append(("get", k))
        return dict.get(self, k, d)

class Meta(type):
    def __instancecheck__(cls, o):
        for _ in (): pass
        log.append("check")
        return type(o) is P

class Like(metaclass=Meta):
    __match_args__ = ("x",)

class Prop:
    __match_args__ = ("v",)
    @property
    def v(self):
        for _ in (): pass
        log.append("v")
        return 7

class C:
    K = P(1)

class Boom:
    def __eq__(self, o):
        for _ in (): pass
        raise KeyError("boom")

class B:
    K = Boom()

def f(v):
    match v:
        case C.K: return "K"
        case [a, b]: return ("seq", a, b)
        case {"k": a}: return ("map", a)
        case Like(3): return "like3"
        case Prop(7): return "prop7"
        case _: return "other"

def run():
    out = []
    for v in (P(1), Seq([4, 5]), Map(k=6), P(3), Prop(), 9):
        log.clear()
        out.append((f(v), list(log)))
    return out

expected = [("K", [("eq", 1)]),
            (("seq", 4, 5), [("eq", 1), "len"]),
            (("map", 6), [("eq", 1), ("get", "k")]),
            ("like3", [("eq", 3), "check"]),
            ("prop7", [("eq", 1), "check", "v"]),
            ("other", [("eq", 1), "check"])]
assert_eq(run(), expected)
for v, (result, calls) in zip((P(1), Seq([4, 5]), Map(k=6), P(3), Prop(), 9), expected):
    log.clear()
    assert_eq((f(v), log), (result, calls))

def raises():
    caught = None
    try:
        match 1:
            case B.K: caught = "matched"
            case bound: caught = "bound"
    except KeyError as e:
        caught = e.args
    return caught

assert_eq(raises(), ("boom",))
try:
    match 1:
        case [*rest] if rest: pass
        case B.K as kept: pass
except KeyError as e:
    assert_eq(e.args, ("boom",))
assert_eq("kept" in globals(), False)
