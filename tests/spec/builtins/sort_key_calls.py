# spec: PLS-315 25.1.4, 19.3.34
# description: a sort's key is a separate call for each item, in order:
# each call's locals start unbound, a closure made in one call keeps that
# call's item, a key with a default or a second parameter binds afresh,
# a generator key gives a new generator per item, and a key that raises
# part way restores the list and propagates. Inside functions and
# generators as at module level.
from harness import *

def cases():
    out = []
    # Locals start unbound in every call: the first item binds y, later ones do not.
    seen = []
    def unbound(x):
        if x == 3: y = x
        try: seen.append(y)
        except NameError: seen.append("unbound")
        return -x
    out.append((sorted([3, 1, 2], key=unbound), seen))
    # A closure made in one call keeps that call's item.
    made = []
    def closing(x):
        made.append(lambda: x)
        return x % 3
    out.append((sorted(range(6), key=closing), [f() for f in made]))
    # A default, and a keyword-only parameter with a default, bind each time.
    def defaulted(x, scale=2, *, shift=1):
        scale += x
        return scale + shift
    out.append(sorted([5, 0, 3], key=defaulted))
    # A generator function gives a new generator for each item.
    def gen(x):
        yield x
    keys = []
    def via(x):
        g = gen(x)
        keys.append(g)
        return next(g)
    out.append((sorted([2, 0, 1], key=via), len(set(map(id, keys)))))
    # A key that raises on the third item: the list is restored, the error propagates.
    items = [4, 1, 3, 2]
    calls = []
    def failing(x):
        calls.append(x)
        if len(calls) == 3: raise ValueError(x)
        return x
    try: items.sort(key=failing)
    except ValueError as e: out.append(("raised", e.args, items, calls))
    # The same key again after the failure.
    out.append(sorted(items, key=lambda v: -v))
    return out

expected = [([3, 2, 1], [3, "unbound", "unbound"]),
            ([0, 3, 1, 4, 2, 5], [0, 1, 2, 3, 4, 5]),
            [0, 3, 5],
            ([0, 1, 2], 3),
            ("raised", (3,), [4, 1, 3, 2], [4, 1, 3]),
            [4, 3, 2, 1]]
assert_eq(cases(), expected)

def g():
    yield cases()
assert_eq(next(g()), expected)
