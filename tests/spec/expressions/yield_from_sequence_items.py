# spec: PLS-315 13.16.3, 27.2.2
# description: A generator's yield from of a list, tuple or range gives
# each item to next(), a for loop and the builtins that consume it, a
# list grown meanwhile giving the new items too; once the sequence ends
# the yield from's value is None and the code after it runs, the
# generator then raising StopIteration with its return value, inside
# functions as at module level.
from harness import *

log = []

def over(items, tag):
    got = yield from items
    log.append((tag, got))
    return tag

def growing():
    items = [1, 2]
    g = over(items, "grown")
    out = []
    for v in g:
        out.append(v)
        if v < 4: items.append(v + 2)
    return out

def stopped():
    g = over((7,), "tuple")
    first = next(g)
    try:
        next(g)
    except StopIteration as e:
        return first, e.value

def results():
    del log[:]
    return [sum(over([1, 2, 3], "sum")), list(over(range(4), "range")),
            [v for v in over((5, 6), "loop")], growing(), stopped(),
            list(zip(over("ab", "str"), over(range(10, 12), "zip"))),
            max(over(range(-3, 3, 2), "max")), list(log)]

expected = [6, [0, 1, 2, 3], [5, 6], [1, 2, 3, 4, 5], (7, "tuple"),
            [("a", 10), ("b", 11)], 1,
            [("sum", None), ("range", None), ("loop", None), ("grown", None), ("tuple", None), ("str", None), ("max", None)]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
