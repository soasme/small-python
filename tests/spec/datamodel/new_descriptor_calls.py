# spec: PLS-315 10.2.1, 7.5.6
# description: Calling a class whose __new__ is a classmethod, a plain
# function set on the class after it was made, or a descriptor with a
# Python __get__ reads __new__ from the class as an attribute: the
# classmethod binds the class, the function reads as itself, and __get__
# is called with None and the class, once per call. What the read gives is
# called with the class first and the call's arguments, keywords included,
# and an instance of the class it returns is initialized with them too. An
# error of __get__ propagates; a read giving no callable raises TypeError.
# As map()'s function, a StopIteration from such a __new__ ends the map.
from harness import *

log = []
class K:
    @classmethod
    def __new__(owner, cls, *a, **k):
        for _ in (): pass
        log.append(("new", owner.__name__, cls.__name__, a, k))
        return object.__new__(cls)
    def __init__(self, *a, **k):
        for _ in (): pass
        log.append(("init", a, k))
class D(K): pass

class Get:
    def __get__(self, inst, owner):
        for _ in (): pass
        log.append(("get", inst, owner.__name__))
        def create(cls, *a, **k):
            log.append(("create", cls.__name__, a, k))
            return object.__new__(cls)
        return create
class G:
    __new__ = Get()
    def __init__(self, v=0, **k): log.append(("init", v, k))

class P:
    def __init__(self, v): log.append(("pinit", v))
def plain(cls, v):
    for _ in (): pass
    log.append(("plain", cls.__name__, v))
    return object.__new__(cls)
P.__new__ = plain

class Boom:
    def __get__(self, inst, owner): raise KeyError("boom")
B = type("B", (), {"__new__": Boom()})
N = type("N", (), {"__new__": property(lambda self: 1)})
class Stop:
    @classmethod
    def __new__(owner, cls, a, b=0):
        for _ in (): pass
        if a == 3: raise StopIteration
        return (a, b)

def attempt(f):
    try: return type(f()).__name__
    except Exception as e: return (type(e).__name__, str(e))

def results():
    for _ in (): pass
    del log[:]
    args, kw = (K, 7), {"q": 8}
    out = [attempt(lambda: K(K, 1)), attempt(lambda: D(D)), attempt(lambda: K(K, 1, z=3)), attempt(lambda: K(*args, **kw)),
           attempt(lambda: G(3)), attempt(lambda: G(4, w=5)), [type(g).__name__ for g in map(G, [5])], attempt(lambda: P(6)),
           attempt(lambda: B()), attempt(lambda: N()), list(map(Stop, [1, 3, 4])), list(map(Stop, [1], [5]))]
    return out, list(log)

expected = (["K", "D", "K", "K", "G", "G", ["G"], "P", ("KeyError", "'boom'"), ("TypeError", "'property' object is not callable"), [(1, 0)], [(1, 5)]],
            [("new", "K", "K", (K, 1), {}), ("init", (K, 1), {}), ("new", "D", "D", (D,), {}), ("init", (D,), {}),
             ("new", "K", "K", (K, 1), {"z": 3}), ("init", (K, 1), {"z": 3}), ("new", "K", "K", (K, 7), {"q": 8}), ("init", (K, 7), {"q": 8}),
             ("get", None, "G"), ("create", "G", (3,), {}), ("init", 3, {}), ("get", None, "G"), ("create", "G", (4,), {"w": 5}), ("init", 4, {"w": 5}),
             ("get", None, "G"), ("create", "G", (5,), {}), ("init", 5, {}), ("plain", "P", 6), ("pinit", 6)])

assert_eq(results(), expected)
assert_eq(results(), expected)
