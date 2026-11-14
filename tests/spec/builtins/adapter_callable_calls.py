# spec: PLS-315 27.1.3, 27.1.4, 27.1.6, 27.1.8, 19.3.27
# description: enumerate, zip and map over a callable iterator
# iter(f, sentinel) of a Python function f, which may loop, call f for
# each item, in order, also beside str, list and range iterators before
# or after it and in a for loop, a comprehension or a consumer; the
# sentinel, or a StopIteration from f, ends the iterator and the adapter,
# a zip after taking the earlier iterables' items, and the iterator stays
# ended; any other exception propagates; next() of such an adapter takes
# one item. Inside functions as at module level.
from harness import *

n = [0]
log = []

def f():
    for _ in (): pass
    n[0] += 1
    log.append(n[0])
    if n[0] == 50: raise StopIteration
    if n[0] == 60: raise LookupError("f")
    return n[0]

def at(k):
    n[0] = k
    return f

def adapters():
    out = []
    out.append(list(zip(iter(at(0), 3), "abc")))
    out.append([x for x in zip("xyz", iter(at(0), 3))])
    out.append(list(enumerate(iter(at(0), 4))))
    out.append(dict(zip(iter(at(0), 9), iter(f, 9))))
    it = iter(at(0), 2)
    z = zip("pq", it)
    out.append((next(z), list(z), list(it)))
    out.append(list(zip(iter(at(45), 0), range(10))))
    out.append(list(map(lambda a, b: a + b, iter(at(0), 4), iter(f, 6))))
    out.append(list(zip([7, 8], iter(at(0), 9), "uv")))
    t = 0
    for i, x in enumerate(iter(at(0), 3)): t += i * x
    out.append(t)
    return out

expected = [[(1, "a"), (2, "b")], [("x", 1), ("y", 2)], [(0, 1), (1, 2), (2, 3)],
            {1: 2, 3: 4, 5: 6, 7: 8}, (("p", 1), [], []), [(46, 0), (47, 1), (48, 2), (49, 3)],
            [3, 7], [(7, 1, "u"), (8, 2, "v")], 2]
expected_log = [1, 2, 3, 1, 2, 3, 1, 2, 3, 4, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2,
                46, 47, 48, 49, 50, 1, 2, 3, 4, 5, 6, 1, 2, 1, 2, 3]
assert_eq(adapters(), expected)
assert_eq(log, expected_log)
log.clear()

assert_eq(list(zip("xyz", iter(at(0), 3))), [("x", 1), ("y", 2)])
assert_eq(log, [1, 2, 3])

def errors():
    try: list(zip("abc", iter(at(58), 0)))
    except LookupError as e: return e.args, n[0]

assert_eq(errors(), (("f",), 60))
