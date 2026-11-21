# spec: PLS-315 10.2.1, 7.3.3
# description: A class call reads an __init__ that a descriptor gives on
# the new instance: a property's getter or a descriptor's Python __get__,
# which may loop, gives the function the arguments go to, its error
# passing out; this holds for keywords, unpacked arguments, subclasses,
# a metaclass's type.__call__, and list and exception bases.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
def booh(self):
    for _ in (): pass
    log.append("booh"); raise AttributeError("booh")
class I:
    __init__ = property(booh)
try: I()
except AttributeError as e: emit("attribute error", e, log)
class Init:
    def __get__(self, obj, owner):
        for _ in (): pass
        log.append(("get", type(obj).__name__, owner.__name__))
        def bound(*a, **k):
            for _ in (): pass
            log.append(("init", a, k)); obj.made = a
        return bound
class J:
    __init__ = Init()
log.clear(); emit(J(1, 2, k=3).made, log)
log.clear(); emit(J(*(4, 5)).made, log)
class Returns:
    def __get__(self, obj, owner): return lambda *a: 5
class R:
    __init__ = Returns()
try: R()
except TypeError as e: emit("type error", e)
class Sub(J): pass
log.clear(); emit(Sub(7).made, log)
class Meta(type):
    def __call__(cls, *a, **k):
        for _ in (): pass
        log.append("meta")
        return type.__call__(cls, *a, **k)
class K(metaclass=Meta):
    __init__ = Init()
log.clear(); emit(K(8).made, log)
log.clear(); emit(type.__call__(J, 9).made, log)
class L(list):
    __init__ = Init()
log.clear(); l = L([1]); emit(l, l.made, log)
class E(Exception):
    __init__ = Init()
log.clear(); e = E(2); emit(e.args, e.made, log)
EXPECTED = [
    "attribute error booh ['booh']",
    "(1, 2) [('get', 'J', 'J'), ('init', (1, 2), {'k': 3})]",
    "(4, 5) [('get', 'J', 'J'), ('init', (4, 5), {})]",
    "type error __init__() should return None, not 'int'",
    "(7,) [('get', 'Sub', 'Sub'), ('init', (7,), {})]",
    "(8,) ['meta', ('get', 'K', 'K'), ('init', (8,), {})]",
    "(9,) [('get', 'J', 'J'), ('init', (9,), {})]",
    "[] ([1],) [('get', 'L', 'L'), ('init', ([1],), {})]",
    "(2,) (2,) [('get', 'E', 'E'), ('init', (2,), {})]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
