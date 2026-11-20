# spec: PLS-315 10.3, 7.3.2, 7.7.1, 13.10
# description: iter() and in read a class's __iter__ or __contains__
# descriptor, whose Python getter runs once and whose result is called.
# A read raising AttributeError leaves the method absent: iter() falls
# back to the sequence protocol of a __getitem__, else raises TypeError;
# in falls back to iteration, by __iter__ or __getitem__, else raises
# TypeError; any other error propagates. A __contains__ result is taken
# by its truth, also in a test or a chain.
from harness import *

log = []
def booh(self): raise AttributeError("booh")
def boom(self): raise KeyError("boom")
def gives(r):
    def get(self):
        for _ in (): pass
        log.append("get")
        return lambda *x: r
    return property(get)
def it(self):
    for _ in (): pass
    log.append("iter")
    return iter([1, 2])
def attempt(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))

IA = type("IA", (), {"__iter__": property(booh)})
IB = type("IB", (), {"__iter__": property(booh), "__getitem__": lambda s, i: [7, 8][i]})
IC = type("IC", (), {"__iter__": property(boom)})
ID = type("ID", (), {"__iter__": gives(None)})
IE = type("IE", (), {"__iter__": gives(5)})
A = type("A", (), {"__contains__": property(booh)})
B = type("B", (), {"__contains__": property(booh), "__iter__": it})
C = type("C", (), {"__contains__": property(booh), "__getitem__": lambda s, i: [5][i]})
D = type("D", (), {"__contains__": property(boom)})
E = type("E", (), {"__contains__": gives(0)})
F = type("F", (), {"__contains__": gives("yes")})

def run():
    for _ in (): pass
    del log[:]
    out = [attempt(lambda: iter(IA())), attempt(lambda: list(iter(IB()))), attempt(lambda: iter(IC())),
           attempt(lambda: iter(ID())), attempt(lambda: iter(IE())),
           attempt(lambda: 1 in A()), attempt(lambda: 2 in B()), attempt(lambda: 3 not in B()), attempt(lambda: 5 in C()),
           attempt(lambda: 1 in D()), attempt(lambda: 1 in E()), attempt(lambda: 1 not in F())]
    try: out.append(2 in B())
    except Exception as e: out.append(type(e).__name__)
    try: out.append(1 if 2 in B() else 0)
    except Exception as e: out.append(type(e).__name__)
    try: out.append(0 < 2 in B())
    except Exception as e: out.append(type(e).__name__)
    return out, list(log)

expected = ([("TypeError", "'IA' object is not iterable"), [7, 8], ("KeyError", "'boom'"),
             ("TypeError", "ID.__iter__() must return an iterator, not NoneType"),
             ("TypeError", "IE.__iter__() must return an iterator, not int"),
             ("TypeError", "argument of type 'A' is not a container or iterable"), True, True, True, ("KeyError", "'boom'"),
             False, False, True, 1, True],
            ["get", "get", "iter", "iter", "get", "get", "iter", "iter", "iter"])

assert_eq(run(), expected)
assert_eq(run(), expected)
