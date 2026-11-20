# spec: PLS-315 10.3, 7.3.2, 7.7.1, 27.1.2
# description: A class whose __getitem__ is a descriptor iterates by the
# sequence protocol: each item reads it through its getter, then calls
# what the read returned with the index, from 0 until IndexError, in a
# loop, a comprehension, list(), next(), in, zip() and on a metaclass's
# classes alike; an error of the read, AttributeError too, propagates
# from that item and leaves the iterator at its index.
from harness import *

log = []
def booh(self): raise AttributeError("booh")
def gives(items):
    def get(self):
        for _ in (): pass
        log.append("get")
        def item(i):
            log.append(("item", i))
            return items[i]
        return item
    return property(get)
class Reads:
    def __get__(self, obj, owner):
        log.append("Reads")
        return lambda i: [7, 8][i]
A = type("A", (), {"__getitem__": gives([1, 2])})
B = type("B", (), {"__getitem__": property(booh)})
C = type("C", (), {"__getitem__": Reads()})
M = type("M", (type,), {"__getitem__": gives(["m"])})
def attempt(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))
def run():
    for _ in (): pass
    del log[:]
    out = [attempt(lambda: list(A())), attempt(lambda: [x for x in A()]), attempt(lambda: next(iter(A()))),
           attempt(lambda: list(B())), attempt(lambda: next(iter(B()))), attempt(lambda: list(C())),
           attempt(lambda: 2 in A()), attempt(lambda: list(zip(A(), "ab"))), attempt(lambda: dict(A())),
           attempt(lambda: list(reversed(A()))), attempt(lambda: list(M("X", (), {}))), attempt(lambda: A()[1])]
    for x in A(): out.append(x)
    it = iter(B())
    out.append(attempt(lambda: next(it))); out.append(attempt(lambda: next(it)))
    return out, list(log)

expected = ([[1, 2], [1, 2], 1, ('AttributeError', 'booh'), ('AttributeError', 'booh'), [7, 8], True, [(1, 'a'), (2, 'b')], ('TypeError', 'object is not iterable'), ('TypeError', "object of type 'A' has no len()"), ['m'], 2, 1, 2, ('AttributeError', 'booh'), ('AttributeError', 'booh')], ['get', ('item', 0), 'get', ('item', 1), 'get', ('item', 2), 'get', ('item', 0), 'get', ('item', 1), 'get', ('item', 2), 'get', ('item', 0), 'Reads', 'Reads', 'Reads', 'get', ('item', 0), 'get', ('item', 1), 'get', ('item', 0), 'get', ('item', 1), 'get', ('item', 2), 'get', ('item', 0), 'get', ('item', 0), 'get', ('item', 1), 'get', ('item', 1), 'get', ('item', 0), 'get', ('item', 1), 'get', ('item', 2)])

assert_eq(run(), expected)
assert_eq(run(), expected)
