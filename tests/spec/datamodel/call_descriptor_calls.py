# spec: PLS-315 10.3, 7.3.2, 13.3.4
# description: Calling an instance whose class's __call__ is a
# descriptor reads it through its getter, once per call, then calls what
# the read returned with the call's arguments, keywords included; an
# error of the read, AttributeError too, propagates, there being no
# fallback. callable() is true for such an instance by the class's
# __call__ alone, without reading it, also for __call__ = None.
from harness import *

log = []
def booh(self): raise AttributeError("booh")
def boom(self): raise KeyError("boom")
def gives(r):
    def get(self):
        for _ in (): pass
        log.append("get")
        return lambda *a, **k: (r, a, k)
    return property(get)

class Reads:
    def __get__(self, obj, owner):
        for _ in (): pass
        log.append(("get", type(obj).__name__, owner.__name__))
        return lambda *a: ("read", a)

A = type("A", (), {"__call__": property(booh)})
B = type("B", (), {"__call__": property(boom)})
C = type("C", (), {"__call__": gives(1)})
D = type("D", (), {"__call__": Reads()})
N = type("N", (), {"__call__": None})
class S(int):
    __call__ = gives(2)

def attempt(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))

def results():
    for _ in (): pass
    del log[:]
    out = [attempt(lambda: A()()), attempt(lambda: B()(1)), attempt(lambda: C()(1, 2)), attempt(lambda: C()(3, x=4)),
           attempt(lambda: D()(5)), attempt(lambda: S(6)(7)), attempt(lambda: N()()),
           [callable(A()), callable(B()), callable(N()), callable(S(1))]]
    return out, list(log)

expected = ([("AttributeError", "booh"), ("KeyError", "'boom'"), (1, (1, 2), {}), (1, (3,), {"x": 4}),
             ("read", (5,)), (2, (7,), {}), ("TypeError", "'NoneType' object is not callable"),
             [True, True, True, True]],
            ["get", "get", ("get", "D", "D"), "get"])

assert_eq(results(), expected)
assert_eq(results(), expected)
