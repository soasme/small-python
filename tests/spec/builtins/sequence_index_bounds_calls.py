# spec: PLS-315 25.5.2, 25.1.3
# description: index of an item in a list or tuple with a start, or a
# start and a stop, compares only the items from start up to stop, each by
# its Python __eq__, which may loop: a negative bound counts from the end
# and is clipped at zero, a bound past the end, a bool or a huge int
# clips to the length, a missing item raises ValueError, an exception
# from __eq__ propagates, and a comparison that shortens the list ends
# the search at its new end. Inside functions as at module level.
from harness import *

log = []

class Item:
    def __init__(self, n): self.n = n
    def __eq__(self, other):
        for _ in range(2): pass
        log.append(self.n)
        if other == "bad": raise LookupError(self.n)
        if other == "cut": del items[2:]
        return self.n == other

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def searches():
    global items
    del log[:]
    items = [Item(0), Item(1), Item(2), Item(1), Item(4)]
    t = tuple(items)
    out = [items.index(1, 2), items.index(1, -2), t.index(1, 0, 2), t.index(4, -9, 99), items.index(2, True),
           error(lambda: items.index(1, 1, 1)), error(lambda: items.index(4, 0, -1)), error(lambda: t.index(0, 2 ** 100)),
           items.index(0, -2 ** 100), error(lambda: items.index("bad", 3)), list(log)]
    del log[:]
    out += [error(lambda: items.index("cut", 1, 4)), len(items), list(log)]
    return out

expected = [3,
            3,
            1,
            4,
            2,
            ('ValueError', 'list.index(x): x not in list'),
            ('ValueError', 'list.index(x): x not in list'),
            ('ValueError', 'tuple.index(x): x not in tuple'),
            0,
            ('LookupError', '1'),
            [2, 1, 1, 0, 1, 0, 1, 2, 1, 4, 1, 2, 0, 1, 2, 1, 0, 1],
            ('ValueError', 'list.index(x): x not in list'),
            2,
            [1]]

def main():
    return searches()

assert_eq(main(), expected)
assert_eq(searches(), expected)
