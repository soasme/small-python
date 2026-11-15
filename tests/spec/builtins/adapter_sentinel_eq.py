# spec: PLS-315 27.1.3, 27.1.4, 27.1.6, 27.1.8
# description: zip(), map() and enumerate() of a callable iterator
# iter(f, sentinel) compare each result of f with the sentinel by the
# sentinel's Python __eq__, which may loop, before making their item; a
# true comparison ends the adapter's items, an error from __eq__
# propagates. For loops, comprehensions, consumers, generator
# expressions and next(), inside functions as at module level.
from harness import *

log = []

class S:
    def __init__(self, n): self.n = n
    def __eq__(self, other):
        for _ in (): pass
        log.append((self.n, other))
        if other is -1: raise KeyError("eq")
        return other == self.n

def counter(xs):
    it = iter(xs)
    return lambda: next(it)

def adapts():
    out = [[a for a in zip(iter(counter([1, 2, 3]), S(3)), "abc")],
           list(map(lambda x: x * 2, iter(counter([1, 2, 3]), S(2)))),
           list(enumerate(iter(counter([4, 5]), S(9))))]
    z = zip("xy", iter(counter([7, 8, 9]), S(8)))
    out.append((next(z), list(z)))
    try: list(zip(iter(counter([1, -1]), S(5))))
    except KeyError as e: out.append(e.args)
    out.append(sum(x for x, y in zip(iter(counter([1, 2, 3, 4]), S(4)), range(9))))
    r = []
    for a, b in zip(iter(counter([1, 2, 3]), S(3)), iter(counter([4, 5, 6]), S(6))): r.append(a + b)
    out.append(r)
    return out

expected = [[(1, "a"), (2, "b")], [2], [(0, 4), (1, 5)], (("x", 7), []), ("eq",), 6, [5, 7]]
expected_log = [(3, 1), (3, 2), (3, 3), (2, 1), (2, 2), (9, 4), (9, 5), (8, 7), (8, 8), (5, 1), (5, -1),
                (4, 1), (4, 2), (4, 3), (4, 4), (3, 1), (6, 4), (3, 2), (6, 5), (3, 3)]
assert_eq(adapts(), expected)
assert_eq(log, expected_log)
log.clear()

assert_eq([a for a in enumerate(iter(counter([7, 8]), S(8)))], [(0, 7)])
assert_eq(log, [(8, 7), (8, 8)])
