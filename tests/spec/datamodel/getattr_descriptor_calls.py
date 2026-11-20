# spec: PLS-315 10.3, 7.3.2, 7.3.4
# description: A class whose __getattr__ is a descriptor answers a missing
# attribute by reading it through its getter, after the lookup's
# AttributeError, then calling what the read gave with the name alone.
# An attribute read, a method call, getattr() with or without a default
# and hasattr() agree, also after a Python __getattribute__ or property
# raises AttributeError; an error of the read or the call propagates,
# AttributeError too, where getattr()'s default and hasattr() take it.
from harness import *

log = []
def booh(self): raise AttributeError("booh")
def boom(self): raise KeyError("boom")
def gives(tag):
    def get(self):
        for _ in (): pass
        log.append(("get", tag))
        def answer(name):
            log.append(("call", name))
            if name == "bad": raise AttributeError("no " + name)
            return (tag, name)
        return answer
    return property(get)

class Reads:
    def __get__(self, obj, owner):
        log.append(("Reads", type(obj).__name__, owner.__name__))
        return lambda name: ("R", name)

def missing(self, name):
    log.append(("getattribute", name))
    raise AttributeError(name)

C = type("C", (), {"__getattr__": gives("C"), "present": 1, "method": lambda self: "m"})
R = type("R", (), {"__getattr__": Reads()})
H = type("H", (), {"__getattr__": gives("H"), "__getattribute__": missing})
P = type("P", (), {"__getattr__": gives("P"), "p": property(booh)})
A = type("A", (), {"__getattr__": property(booh)})
B = type("B", (), {"__getattr__": property(boom)})

def attempt(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))

def results():
    for _ in (): pass
    del log[:]
    c = C()
    out = [c.present, c.method(), c.x, attempt(lambda: c.y()), getattr(c, "z"), getattr(c, "w", 0),
           hasattr(c, "v"), attempt(lambda: c.bad), getattr(c, "bad", "dflt"), hasattr(c, "bad"),
           R().x, getattr(R(), "y"), H().x, getattr(H(), "y", 0), P().p, P().q,
           attempt(lambda: A().x), getattr(A(), "x", "dflt"), hasattr(A(), "x"),
           attempt(lambda: B().x), attempt(lambda: getattr(B(), "x", 0)), attempt(lambda: hasattr(B(), "x"))]
    return out, list(log)

expected = ([1, "m", ("C", "x"), ("TypeError", "'tuple' object is not callable"), ("C", "z"), ("C", "w"),
             True, ("AttributeError", "no bad"), "dflt", False,
             ("R", "x"), ("R", "y"), ("H", "x"), ("H", "y"), ("P", "p"), ("P", "q"),
             ("AttributeError", "booh"), "dflt", False,
             ("KeyError", "'boom'"), ("KeyError", "'boom'"), ("KeyError", "'boom'")],
            [("get", "C"), ("call", "x"), ("get", "C"), ("call", "y"), ("get", "C"), ("call", "z"),
             ("get", "C"), ("call", "w"), ("get", "C"), ("call", "v"), ("get", "C"), ("call", "bad"),
             ("get", "C"), ("call", "bad"), ("get", "C"), ("call", "bad"),
             ("Reads", "R", "R"), ("Reads", "R", "R"),
             ("getattribute", "x"), ("get", "H"), ("call", "x"), ("getattribute", "y"), ("get", "H"), ("call", "y"),
             ("get", "P"), ("call", "p"), ("get", "P"), ("call", "q")])

assert_eq(results(), expected)
assert_eq(results(), expected)
