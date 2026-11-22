# spec: PLS-315 13.2.3, 13.2.4, 14.2
# description: A tuple or list display evaluates its items left to right,
# each once; a list display makes a new list each time; when an item
# raises, the items already evaluated are released and nothing is bound.
from harness import *

calls = []


def item(value):
    calls.append(value)
    return value


class Noted:
    def __init__(self, name):
        self.name = name

    def __del__(self):
        calls.append("del " + self.name)


def pair(a, b):
    return item(a), item(b)


assert_same(pair(1, 2), (1, 2))
assert_same(calls, [1, 2])
del calls[:]

row = [item("x"), item("y"), item("z")]
assert_same(row, ["x", "y", "z"])
assert_same(calls, ["x", "y", "z"])
del calls[:]


def fresh():
    return [1, 2]


assert_same(fresh() is fresh(), False)
first = fresh()
first.append(3)
assert_same(fresh(), [1, 2])

big = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19)
assert_same(len(big), 20)
assert_same(big[19], 19)
nested = ((1, 2), [3, (4,)], ())
assert_same(nested, ((1, 2), [3, (4,)], ()))
assert_same(type(nested[1]), list)


def failing():
    return (Noted("a"), 1 // 0)


try:
    bound = failing()
except ZeroDivisionError:
    calls.append("caught")
assert_same(calls, ["del a", "caught"])
assert_same("bound" in globals(), False)
del calls[:]

x, y = 3, 4
swapped = [y, x]
assert_same(swapped, [4, 3])
single = (x,)
assert_same(single, (3,))
