# spec: PLS-315 27.2.2, 10.2.1
# description: throw(type, value, traceback) into a generator suspended at
# a yield makes the exception as throw(type, value) does, the class's
# Python __new__ or __init__, which may loop, first, and gives it the
# traceback before the generator resumes with it: the handler sees a
# __traceback__ whose next entry is the one given. Positional and starred
# arguments; an unhandled exception propagates with it. Inside functions
# as at module level.
from harness import *

log = []

class E(Exception):
    def __init__(self, *a):
        for _ in (): pass
        log.append(("init", a))
        super().__init__(*a)

class N(Exception):
    def __new__(cls, *a):
        for _ in (): pass
        log.append(("new", a))
        return super().__new__(cls, *a)

def gen():
    for _ in (): pass
    try:
        yield 1
    except (E, N) as e:
        yield type(e).__name__, e.args, e.__traceback__.tb_next is tb

try: raise ValueError
except ValueError as e: tb = e.__traceback__

def throws():
    out = []
    for args in ((E, 5, tb), (E, (6, 7), tb), (N, 8, tb), (E, E(9), tb)):
        g = gen(); next(g)
        out.append(g.throw(args[0], args[1], args[2]))
        g = gen(); next(g)
        out.append(g.throw(*args))
    g = gen(); next(g)
    try: g.throw(KeyError, "k", tb)
    except KeyError as e: out.append(("key", e.args, e.__traceback__.tb_next.tb_next is tb))
    return out

expected = [("E", (5,), True)] * 2 + [("E", (6, 7), True)] * 2 + [("N", (8,), True)] * 2 + [("E", (9,), True)] * 2 + \
           [("key", ("k",), True)]
expected_log = [("init", (9,)), ("init", (5,)), ("init", (5,)), ("init", (6, 7)), ("init", (6, 7)), ("new", (8,)), ("new", (8,))]
assert_eq(throws(), expected)
assert_eq(log, expected_log)
log.clear()

g = gen(); next(g)
assert_eq(g.throw(E, 1, tb), ("E", (1,), True))
assert_eq(log, [("init", (1,))])
