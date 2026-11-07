# spec: PLS-315 27.1.5, 26.1.1
# description: filter calls its function once per item in order, keeps
# the items whose result is true, takes an object's __bool__ for that
# truth, ends at a StopIteration from the function, and stops at an
# error while the filter stays usable, its function called with one
# argument; dict takes a generator's pairs one at a time, stopping at the
# first that is not a pair. Inside functions whose callbacks loop, as at
# module level.
from harness import *

log = []
def even(x):
    for _ in range(2): pass
    log.append(x)
    return x % 2 == 0
def stop(x):
    for _ in range(2): pass
    if x == 3: raise StopIteration
    return True
def bad(x):
    for _ in range(2): pass
    if x == 2: raise KeyError(x)
    return x
class Truth:
    def __init__(s, v): s.v = v
    def __bool__(s): return s.v
def obj(x):
    for _ in range(2): pass
    return Truth(x > 1)

def filters():
    out = [list(filter(even, range(7))), [x for x in filter(even, [1, 3, 4])], sum(filter(even, range(5))),
           list(filter(stop, range(6))), list(filter(obj, range(4)))]
    f = filter(bad, range(5))
    try:
        for x in f: out.append(x)
    except KeyError as e: out.append(("key", e.args))
    out.append(list(f))
    g = filter(even, (i for i in range(5)))
    out.append((next(g), list(g)))
    def none():
        for _ in range(2): pass
    try: list(filter(none, [1]))
    except TypeError as e: out.append(str(e))
    return out

assert_eq(filters(), [[0, 2, 4, 6], [4], 6, [0, 1, 2], [2, 3], 1, ("key", (2,)), [3, 4], (0, [2, 4]),
                     "filters.<locals>.none() takes 0 positional arguments but 1 was given"])
assert_eq(log, [0, 1, 2, 3, 4, 5, 6, 1, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4])

taken = []
def pairs(*items):
    for x in items:
        taken.append(x)
        yield x

def dicts():
    out = [dict(pairs((1, 2), [3, 4], "ab")), dict(pairs())]
    for wrong in ((1, 2, 3), 5, (1, [])):
        try: out.append(dict(pairs((0, 0), wrong, (9, 9))))
        except (TypeError, ValueError) as e: out.append((type(e).__name__, str(e), getattr(e, "__notes__", None)))
    class D(dict): pass
    out.append(type(D(pairs((1, 1)))).__name__)
    return out

assert_eq(dicts(), [{1: 2, 3: 4, "a": "b"}, {},
                    ("ValueError", "dictionary update sequence element #1 has length 3; 2 is required", None),
                    ("TypeError", "object is not iterable", ["Cannot convert dictionary update sequence element #1 to a sequence"]),
                    {0: 0, 1: [], 9: 9}, "D"])
assert_eq(taken, [(1, 2), [3, 4], "ab", (0, 0), (1, 2, 3), (0, 0), 5, (0, 0), (1, []), (9, 9), (1, 1)])
