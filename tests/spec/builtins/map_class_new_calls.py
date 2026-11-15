# spec: PLS-315 27.1.6, 10.2.1, 13.3.4
# description: map of a class with a Python __new__, which may loop, calls
# it with the class and each item, then, for an instance of the class, its
# __init__ with the items, in order; a result of another type is the item
# as made, and a builtin subclass's own __init__ runs natively. So does a
# method call whose attribute, read by a Python property getter, is such a
# class, or an instance with a Python __call__. An error from __new__ or
# __init__, or an __init__ returning other than None, propagates. In for
# loops, comprehensions, consumers and zip, inside functions as at module
# level.
from harness import *

log = []

class N:
    def __new__(cls, *a):
        for _ in (): pass
        log.append(("new", a))
        if a == (0,): return "zero"
        if a == (9,): raise LookupError("nine")
        return super().__new__(cls)
    def __init__(self, *a):
        for _ in (): pass
        log.append(("init", a))
        if a == (7,): raise KeyError("seven")
        self.a = a

class NL(list):
    def __new__(cls, *a):
        for _ in (): pass
        log.append(("nl", a))
        return super().__new__(cls)

class R:
    def __new__(cls, *a):
        for _ in (): pass
        return super().__new__(cls)
    def __init__(self, *a):
        for _ in (): pass
        return 1

class Callable:
    def __call__(self, *a):
        for _ in (): pass
        log.append(("callable", a))
        return a

class H:
    @property
    def n(self):
        for _ in (): pass
        return N
    @property
    def c(self):
        for _ in (): pass
        return Callable()

def show(x):
    return x if isinstance(x, (str, list, tuple, int)) else (type(x).__name__, x.a)

def maps():
    out = [[show(x) for x in map(N, [1, 0, 2])]]
    for x in map(N, [3, 4], "ab"): out.append(show(x))
    out.append(list(map(NL, [[5]])))
    out.append([(show(x), y) for x, y in zip(map(N, [6]), "z")])
    h = H()
    out.append([show(h.n(8)), show(h.n(0)), h.c(1, 2)])
    return out

expected = [[("N", (1,)), "zero", ("N", (2,))], ("N", (3, "a")), ("N", (4, "b")), [[5]], [(("N", (6,)), "z")],
            [("N", (8,)), "zero", (1, 2)]]
expected_log = [("new", (1,)), ("init", (1,)), ("new", (0,)), ("new", (2,)), ("init", (2,)), ("new", (3, "a")), ("init", (3, "a")),
                ("new", (4, "b")), ("init", (4, "b")), ("nl", ([5],)), ("new", (6,)), ("init", (6,)), ("new", (8,)), ("init", (8,)),
                ("new", (0,)), ("callable", (1, 2))]
assert_eq(maps(), expected)
assert_eq(log, expected_log)
log.clear()

assert_eq([show(x) for x in map(N, [1, 0, 2])], expected[0])
assert_eq(log, expected_log[:5])
log.clear()

def errors():
    out, h = [], H()
    for bad in (lambda: list(map(N, [9])), lambda: list(map(N, [7])), lambda: list(map(R, [1])), lambda: h.n(9), lambda: h.n(7)):
        try: bad()
        except Exception as e: out.append((type(e).__name__, str(e)))
    return out

assert_eq(errors(), [("LookupError", "nine"), ("KeyError", "'seven'"), ("TypeError", "__init__() should return None, not 'int'"),
                     ("LookupError", "nine"), ("KeyError", "'seven'")])
assert_eq(log, [("new", (9,)), ("new", (7,)), ("init", (7,)), ("new", (9,)), ("new", (7,)), ("init", (7,))])
