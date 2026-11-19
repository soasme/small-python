# spec: PLS-315 27.2.2, 27.2.3, 10.2.1
# description: throw(cls, value) or throw(cls, value, traceback) of a
# GeneratorExit class whose __init__ is Python, into a generator
# delegating through yield from, closes the delegates first, innermost
# first, then makes the exception of the value's arguments: a tuple's
# items, none for None, else the value; the traceback given is its
# __traceback__. It raises at the outermost yield from, chained to what
# that handles; an error its __init__ raises is raised there instead.
from harness import *

log = []

class Exit(GeneratorExit):
    def __init__(self, *a):
        for _ in (): pass
        log.append(("exit", a))
        if a == ("bad",): raise KeyError("bad init")
        super().__init__(*a)

def inner():
    try: yield 1
    finally: log.append("inner finally")

def mid():
    try: yield from inner()
    finally: log.append("mid finally")

def outer():
    try:
        try: raise IndexError("handled")
        except IndexError: yield from mid()
    except BaseException as e:
        log.append(("outer", type(e).__name__, e.args, type(e.__context__).__name__,
                    e.__traceback__.tb_next is tb if isinstance(e, Exit) else None))
        raise

tb = None
try: raise ValueError
except ValueError as e: tb = e.__traceback__

def throws(*args):
    g = outer(); next(g); log.clear()
    try: r = g.throw(*args)
    except BaseException as e: r = (type(e).__name__, e.args)
    return [r, log[:]]

def results():
    return [throws(Exit, (1, 2)), throws(Exit, None), throws(Exit, 5), throws(Exit, 6, tb), throws(Exit, "bad")]

closed = ["inner finally", "mid finally"]
expected = [
    [("Exit", (1, 2)), closed + [("exit", (1, 2)), ("outer", "Exit", (1, 2), "IndexError", False)]],
    [("Exit", ()), closed + [("exit", ()), ("outer", "Exit", (), "IndexError", False)]],
    [("Exit", (5,)), closed + [("exit", (5,)), ("outer", "Exit", (5,), "IndexError", False)]],
    [("Exit", (6,)), closed + [("exit", (6,)), ("outer", "Exit", (6,), "IndexError", True)]],
    [("KeyError", ("bad init",)), closed + [("exit", ("bad",)), ("outer", "KeyError", ("bad init",), "IndexError", None)]],
]

assert_eq(results(), expected)
def main(): return results()
assert_eq(main(), expected)
