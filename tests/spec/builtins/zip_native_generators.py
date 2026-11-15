# spec: PLS-315 27.1.8, 27.1.6
# description: zip() and map() of builtin iterables, a str, bytes, a dict,
# a range or a list, before a generator take an item from each iterable
# in order, then resume the generator for its item; the zip or map ends
# at the first iterable that ends, items already taken from those before
# it consumed, and those after it untouched. With list, dict, sum and a
# for loop consuming them, inside functions as at module level.
from harness import *

log = []

def g(n):
    for i in range(n):
        log.append(i)
        yield i

def results():
    del log[:]
    it = iter("abc")
    out = [list(zip("ab", g(2))), dict(zip(b"xy", g(3))), sum(map(pow, range(3), g(5))),
           list(zip({1: 2, 3: 4}, [5, 6], g(9)))]
    out.append(list(zip(it, g(1))))
    out.append(next(it))
    after = iter([7, 8])
    out.append(list(zip("a", g(0), after)))
    out.append(list(after))
    pairs = []
    for a, b in zip(range(10, 13), g(2)): pairs.append(a + b)
    out += [pairs, list(log)]
    return out

expected = [[("a", 0), ("b", 1)], {120: 0, 121: 1}, 6, [(1, 5, 0), (3, 6, 1)], [("a", 0)], "c", [], [7, 8], [10, 12],
            [0, 1, 0, 1, 0, 1, 2, 0, 1, 0, 0, 1]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
