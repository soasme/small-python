# spec: PLS-315 13.16.3, 27.2.2, 10.2.1
# description: throw() of an exception class into a generator waiting in
# a yield from of a builtin iterator makes the exception, the class's
# Python __init__, which may loop, first, with the value given, and
# raises it at the yield from; a traceback given becomes its
# __traceback__'s next entry. Its handler may yield; an unhandled one
# propagates. One, two or three arguments; lists, maps and ranges;
# inside functions as at module level.
from harness import *

log = []

class E(Exception):
    def __init__(self, *a):
        for _ in (): pass
        log.append(("init", a))
        super().__init__(*a)

def gen(source):
    try:
        yield from source
    except E as e:
        yield (type(e).__name__, e.args, e.__traceback__.tb_next is tb)

try: raise ValueError
except ValueError as e: tb = e.__traceback__

def throws():
    out = []
    for make in (lambda: [1, 2], lambda: map(str, [1, 2]), lambda: range(3)):
        for args in ((E,), (E, 5), (E, (6, 7), tb), (E, E(8)), (E, None, tb)):
            g = gen(make()); next(g)
            out.append(g.throw(*args))
        g = gen(make()); next(g)
        try: g.throw(KeyError, "k", tb)
        except KeyError as e: out.append((e.args, e.__traceback__.tb_next.tb_next is tb))
    return out

one = [("E", (), False), ("E", (5,), False), ("E", (6, 7), True), ("E", (8,), False), ("E", (), True), (("k",), True)]
# E(8) is made with the argument tuples, before the throws.
one_log = [("init", (8,)), ("init", ()), ("init", (5,)), ("init", (6, 7)), ("init", ())]
assert_eq(throws(), one * 3)
assert_eq(log, one_log * 3)
log.clear()

g = gen([1]); next(g)
assert_eq((g.throw(E, 9), log), (("E", (9,), False), [("init", (9,))]))
