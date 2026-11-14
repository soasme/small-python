# spec: PLS-315 27.1.6, 19.3.3
# description: a map whose function is a class calls the class with the
# next item of each iterable, left to right, as a loop, a consumer or
# another adapter takes each item: the class makes its instance, then
# calls its Python __init__ with the items, which may loop, and the item is
# the instance; an __init__ returning other than None raises TypeError, an
# error from __init__ reaches the caller, a StopIteration from it ends the
# map, and a subclass of a builtin with its own __init__ is called alike.
from harness import *

log = []

class P:
    def __init__(self, *args):
        for _ in (): pass
        log.append(args)
        self.args = args

class Bad:
    def __init__(self, v):
        for _ in (): pass
        return v

class Fails:
    def __init__(self, v):
        for _ in (): pass
        if v == 2: raise LookupError(v)
        log.append(v)

class Stops:
    def __init__(self, v):
        for _ in (): pass
        raise StopIteration(v)

class L(list):
    def __init__(self, v):
        for _ in (): pass
        log.append(("L", v))
        super().__init__([v, v])

def gen():
    for v in (1, 2):
        log.append(("y", v))
        yield v

def calls():
    out = []
    for p in map(P, [1, 2], "ab"):
        log.append(("took", p.args))
    out.append(log[:]); log.clear()
    out.append([p.args for p in list(map(P, gen()))])
    out.append(log[:]); log.clear()
    out.append([(i, p.args) for i, p in enumerate(map(P, (3, 4)))])
    out.append(sorted(type(x).__name__ for x in map(L, [5])))
    out.append(list(map(L, [6]))[0])
    out.append(log[:]); log.clear()
    return out

assert_eq(calls(), [
    [(1, "a"), ("took", (1, "a")), (2, "b"), ("took", (2, "b"))],
    [(1,), (2,)],
    [("y", 1), (1,), ("y", 2), (2,)],
    [(0, (3,)), (1, (4,))],
    ["L"],
    [6, 6],
    [(3,), (4,), ("L", 5), ("L", 6)],
])

def errors():
    out = []
    try: list(map(Bad, [None, 1]))
    except TypeError as e: out.append(str(e))
    try:
        for x in map(Fails, [1, 2, 3]): pass
    except LookupError as e: out.append((e.args, log[:]))
    log.clear()
    try: out.append(list(map(Stops, [1])))
    except StopIteration as e: out.append(("stop", e.args))
    return out

assert_eq(errors(), ["__init__() should return None, not 'int'", ((2,), [1]), []])
