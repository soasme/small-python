# spec: PLS-315 27.2.2, 10.2.1
# description: throw(type, value, None) into a generator suspended at a
# yield behaves as throw(type, value): the class's Python __init__, which
# may loop, makes the exception from the value, a tuple of arguments, one
# argument, None for none, or an instance of the class taken as it is,
# before the generator resumes with it; its handler's yield is the value of
# throw, an unhandled exception propagates, and a third argument other than
# a traceback or None raises TypeError, the generator left suspended.
from harness import *

log = []

class E(Exception):
    def __init__(self, *a):
        for _ in (): pass
        log.append(("init", a))
        super().__init__(*a)

def gen():
    for _ in (): pass
    try:
        yield 1
    except E as e:
        log.append(("caught", e.args))
        yield 2

def throws():
    out = []
    for value in (5, (6, 7), None):
        g = gen(); next(g)
        out.append(g.throw(E, value, None))
    g = gen(); next(g)
    out.append(g.throw(E, E(8), None))
    g = gen(); next(g)
    try: g.throw(KeyError, "k", None)
    except KeyError as e: out.append(("key", e.args))
    g = gen(); next(g)
    try: g.throw(E, 1, 5)
    except TypeError as e: out.append((str(e), next(g, "end")))
    out.append(log[:])
    return out

assert_eq(throws(), [2, 2, 2, 2, ("key", ("k",)), ("throw() third argument must be a traceback object", "end"),
                     [("init", (5,)), ("caught", (5,)), ("init", (6, 7)), ("caught", (6, 7)), ("init", ()), ("caught", ()),
                      ("init", (8,)), ("caught", (8,))]])
