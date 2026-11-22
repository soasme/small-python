# spec: PLS-315 13.3.1, 13.3.2, 13.7, 13.10, 13.17
# description: An operator on names, literals, items and attributes reads
# each operand once and calls each special method once, whether its
# operands are numbers or objects whose methods, properties or missing
# names decide the result.
from harness import *

calls = []


class Logged:
    def __init__(self, value):
        self.value = value

    def __add__(self, other):
        calls.append("add")
        return self.value + other

    def __eq__(self, other):
        calls.append("eq")
        return self.value == other

    def __lt__(self, other):
        calls.append("lt")
        return self.value < other

    __hash__ = None


class Holder:
    def __init__(self):
        self.plain = 2

    @property
    def computed(self):
        calls.append("get")
        return 3


def numbers(x, items):
    return x + 1, items[0] * x, x < items[1], items[1] in items


assert_same(numbers(2, [3, 4]), (3, 6, True, True))

logged = Logged(5)
assert_same(logged + 1, 6)
assert_same(calls, ["add"])
del calls[:]
assert_same(logged == 5, True)
assert_same(calls, ["eq"])
del calls[:]
row = [logged]
assert_same(row[0] < 6, True)
assert_same(calls, ["lt"])
del calls[:]
assert_same(5 in row, True)
assert_same(calls, ["eq"])
del calls[:]

holder = Holder()
assert_same(holder.plain + holder.computed, 5)
assert_same(calls, ["get"])
del calls[:]
if holder.computed < holder.plain:
    fail("3 < 2")
assert_same(calls, ["get"])
del calls[:]


def missing():
    return absent + 1


assert_raises(NameError, missing)
assert_same("ab" + "c", "abc")
assert_same([1, 2] < [1, 3], True)
assert_same((1, 2)[1] + 1, 3)
try:
    1 // 0
except ZeroDivisionError:
    pass
else:
    fail("1 // 0 raised nothing")
