# spec: PLS-315 27.1.5, 27.2.2
# description: filter() of a Python function over a generator resumes the
# generator for each item, then calls the function on it: each item is
# tested before the next is made, and kept by the truth of what the
# function returned; a StopIteration from the function ends the filter
# with the items so far, and its other exceptions propagate. In list(),
# sum(), a for loop, a comprehension and next(), inside functions as at
# module level.
from harness import *

log = []

def gen(*items):
    for item in items:
        for _ in (): pass
        log.append(("y", item))
        yield item

def odd(x):
    for _ in (): pass
    log.append(("t", x))
    if x == 9: raise StopIteration
    return x % 2

def bad(x): raise ValueError(x)

def run():
    out = [list(filter(odd, gen(1, 2, 3))), sum(filter(odd, gen(5, 6))), [y for y in filter(odd, gen(7, 8))]]
    for y in filter(odd, gen(2, 3)): out.append(y)
    f = filter(odd, gen(1, 4, 5))
    out += [next(f), list(f), list(filter(odd, gen(1, 9, 3)))]
    try: list(filter(bad, gen(4)))
    except ValueError as e: out.append(e.args)
    return out

expected = [[1, 3], 5, [7], 3, 1, [5], [1], (4,)]
expected_log = [("y", 1), ("t", 1), ("y", 2), ("t", 2), ("y", 3), ("t", 3), ("y", 5), ("t", 5), ("y", 6), ("t", 6),
                ("y", 7), ("t", 7), ("y", 8), ("t", 8), ("y", 2), ("t", 2), ("y", 3), ("t", 3), ("y", 1), ("t", 1),
                ("y", 4), ("t", 4), ("y", 5), ("t", 5), ("y", 1), ("t", 1), ("y", 9), ("t", 9), ("y", 4)]
assert_eq(run(), expected)
assert_eq(log, expected_log)
log.clear()
assert_eq((list(filter(odd, gen(3, 4))), log), ([3], [("y", 3), ("t", 3), ("y", 4), ("t", 4)]))
