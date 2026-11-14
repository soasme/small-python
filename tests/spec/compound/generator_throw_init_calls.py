# spec: PLS-315 27.2.2, 10.2.1
# description: throw() of an exception class calls the class's Python
# __init__ to make the exception before resuming the generator, also one a
# yield from delegates to, and with a value, the __init__ taking the
# value's tuple of arguments, no argument for None, or the one value, while
# an instance of the class is thrown as it is; an __init__ that returns a
# value other than None
# raises TypeError at the yield instead, and one that raises raises its
# exception there; inside functions as at module level.
from harness import *

log = []

class Made(Exception):
    def __init__(self, *args):
        for i in range(2): pass
        log.append(("init",) + args if args else "init")

class Returns(Exception):
    def __init__(self, *args): return 3

class Raises(Exception):
    def __init__(self, *args): raise KeyError("f", *args)

def gen():
    while True:
        try:
            yield 1
        except GeneratorExit:
            return
        except BaseException as e:
            log.append(("caught", type(e).__name__, e.args))
            if isinstance(e, KeyError): return

def run(*x):
    del log[:]
    g = gen(); next(g)
    try: r = g.throw(*x)
    except BaseException as e: r = ("raised", type(e).__name__, e.args)
    g.close()
    return r, log[:]

def deleg():
    yield from gen()

def runs():
    out = [run(x) for x in (Made, Returns, Raises, KeyError, Made())]
    d = deleg(); next(d); del log[:]
    out.append((d.throw(Made), log[:]))
    d.close()
    return out

expected = [
    (1, ["init", ("caught", "Made", ())]),
    (1, [("caught", "TypeError", ("__init__() should return None, not 'int'",))]),
    (("raised", "StopIteration", ()), [("caught", "KeyError", ("f",))]),
    (("raised", "StopIteration", ()), [("caught", "KeyError", ())]),
    (1, [("caught", "Made", ())]),
    (1, ["init", ("caught", "Made", ())]),
]
assert_eq(runs(), expected)
assert_eq(run(Made), expected[0])

# With a value.
def values():
    out = [run(Made, 5), run(Made, (1, 2)), run(Made, None), run(Returns, 1), run(Raises, (2,))]
    made = Made(9); del log[:]
    out.append(run(Made, made))
    out.append(run(ValueError, 4))
    d = deleg(); next(d); del log[:]
    out.append((d.throw(Made, 3), log[:]))
    d.close()
    return out

expected = [
    (1, [("init", 5), ("caught", "Made", (5,))]),
    (1, [("init", 1, 2), ("caught", "Made", (1, 2))]),
    (1, ["init", ("caught", "Made", ())]),
    (1, [("caught", "TypeError", ("__init__() should return None, not 'int'",))]),
    (("raised", "StopIteration", ()), [("caught", "KeyError", ("f", 2))]),
    (1, [("caught", "Made", (9,))]),
    (1, [("caught", "ValueError", (4,))]),
    (1, [("init", 3), ("caught", "Made", (3,))]),
]
assert_eq(values(), expected)
assert_eq(run(Made, (1, 2)), expected[1])
