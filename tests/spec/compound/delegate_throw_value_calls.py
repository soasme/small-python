# spec: PLS-315 27.2.2, 27.2.3, 10.2.1
# description: throw(type, value) or throw(type, value, traceback) into a
# generator delegating through yield from to generators makes the
# exception by the class's Python __init__ with the value's arguments,
# once, and raises it at the innermost yield, whose handler sees it and
# whose next value the throw returns; an exception the innermost does
# not handle propagates out through each delegate's finally and except.
# A GeneratorExit class, with or without a value, closes the delegates
# first, then is made and raises at the outermost. Inside functions as at module level.
from harness import *

log = []

class Made(Exception):
    def __init__(self, *a):
        for _ in (): pass
        log.append(("init", a))
        super().__init__(*a)

class Exit(GeneratorExit):
    def __init__(self, *a):
        for _ in (): pass
        log.append(("exit", a))
        super().__init__(*a)

def inner():
    try:
        yield 1
    except Made as e:
        log.append(("inner", e.args, e.__traceback__.tb_next is tb if tb else None))
        yield 2
    finally:
        log.append("inner finally")

def mid():
    return (yield from inner())

def outer():
    try: yield from mid()
    except GeneratorExit as e:
        log.append(("outer exit", type(e).__name__, e.args))
        raise
    except KeyError as e:
        log.append(("outer key", e.args))
        yield 3

tb = None
try: raise ValueError
except ValueError as e: tb = e.__traceback__

def throws(args):
    g = outer(); next(g); log.clear()
    try: r = g.throw(*args)
    except BaseException as e: r = ("raised", type(e).__name__, e.args)
    out = [r, log[:]]
    g.close()
    return out

def run():
    global tb
    out = []
    for args in ((Made, 3), (Made, (1, 2)), (Made, None), (KeyError, 6), (Exit, 7)):
        tb = None
        out.append(throws(args))
    tb = e_tb
    out.append(throws((Made, 4, tb)))
    return out

e_tb = tb
expected = [
    [2, [("init", (3,)), ("inner", (3,), None)]],
    [2, [("init", (1, 2)), ("inner", (1, 2), None)]],
    [2, [("init", ()), ("inner", (), None)]],
    [3, ["inner finally", ("outer key", (6,))]],
    [("raised", "Exit", (7,)), ["inner finally", ("exit", (7,)), ("outer exit", "Exit", (7,))]],
    [2, [("init", (4,)), ("inner", (4,), True)]],
]
assert_eq(run(), expected)
tb = None
assert_eq(throws((Made, 8)), [2, [("init", (8,)), ("inner", (8,), None)]])
assert_eq(throws((Exit,)), [("raised", "Exit", ()), ["inner finally", ("exit", ()), ("outer exit", "Exit", ())]])
assert_eq(throws((Exit(9),))[1][-1], ("outer exit", "Exit", (9,)))
