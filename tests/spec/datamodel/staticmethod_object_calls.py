# spec: PLS-315 20.6
# description: a staticmethod object is callable and calls its function
# with the call's arguments as given, positional, starred, keyword or
# double-starred, its defaults filling the rest; the function may loop,
# and its value and exceptions are the call's, a missing argument raising
# the function's TypeError. A staticmethod of a builtin function calls it.
# Inside functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

def pair(x, y=2, *rest, z=3):
    spin(); log.append(x)
    if x == "bad": raise ValueError("bad")
    return (x, y, rest, z)

sm = staticmethod(pair)
length = staticmethod(len)

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def calls():
    del log[:]
    args, kwargs = (5, 6, 7), {"z": 8}
    out = [sm(1), sm(1, 9), sm(*args), sm(4, z=0), sm(*args, **kwargs), sm(x=2), [sm(i)[0] for i in range(2)]]
    out += [error(lambda: sm("bad")), error(lambda: sm()), length("abc"), sm.__func__ is pair, (lambda: sm)()(3)]
    out.append(list(log))
    return out

expected = [(1, 2, (), 3), (1, 9, (), 3), (5, 6, (7,), 3), (4, 2, (), 0), (5, 6, (7,), 8), (2, 2, (), 3), [0, 1],
            ("ValueError", "bad"), ("TypeError", "pair() missing 1 required positional argument: 'x'"), 3, True,
            (3, 2, (), 3), [1, 1, 5, 4, 5, 2, 0, 1, "bad", 3]]

def main():
    return calls()

assert_eq(main(), expected)
assert_eq(calls(), expected)
