# spec: PLS-315 14.2, 14.3, 15.3, 13.17
# description: A one-target assignment of a name or an item of names and
# literals, plain or augmented, evaluates its value and target once and
# calls each special method once, inside and outside a loop body, when its
# values change from numbers to objects between iterations.
from harness import *

calls = []


class Logged:
    def __init__(self, value):
        self.value = value

    def __add__(self, other):
        calls.append("add")
        return self.value + other

    def __iadd__(self, other):
        calls.append("iadd")
        self.value += other
        return self

    def __hash__(self):
        calls.append("hash")
        return hash(self.value)

    def __eq__(self, other):
        calls.append("eq")
        return self.value == (other.value if isinstance(other, Logged) else other)


class Row(list):
    def __setitem__(self, key, value):
        calls.append(("set", key))
        list.__setitem__(self, key, value)

    def __getitem__(self, key):
        calls.append(("get", key))
        return list.__getitem__(self, key)


def numbers(x, row, table):
    total = 0.5
    total += x * x
    y = x + 1
    row[0] = y
    row[-1] += x
    row[1] -= 2.0 * x
    table[x] = y * 2
    table["k"] = x
    count = table[x]
    count += table["k"]
    return total, y, row, table, count


assert_same(numbers(3, [0, 1.0, 2], {}), (9.5, 4, [4, -5.0, 5], {3: 8, "k": 3}, 11))

row = Row([1, 2])
key = 1
row[key] += 5
assert_same(calls, [("get", 1), ("set", 1)])
assert_same(list(row), [1, 7])
del calls[:]

logged = Logged(1)
held = logged
held += 2
assert_same(held is logged and logged.value, 3)
assert_same(calls, ["iadd"])
del calls[:]
plain = logged + 1
assert_same(plain, 4)
assert_same(calls, ["add"])
del calls[:]

table = {}
table[logged] = 1
assert_same(calls, ["hash"])
del calls[:]
same = Logged(3)
table[same] = 2
assert_same(calls, ["hash", "eq"])
assert_same(table[logged], 2)
del calls[:]


def changing(values):
    out = [0]
    for value in values:
        out[0] += value
    return out[0]


assert_same(changing([1, 2, 3]), 6)
assert_same(changing([1, 2.5]), 3.5)
assert_raises(TypeError, changing, [1, [1]])
mixed = [1, 2]
accumulated = Logged(0)
for value in mixed:
    accumulated += value
assert_same(accumulated.value, 3)
assert_same(calls, ["iadd", "iadd"])
del calls[:]


def unbound():
    total += 1
    total = 0


assert_raises(UnboundLocalError, unbound)

counter = 0


def bump(step):
    global counter
    counter += step * 2


bump(3)
assert_same(counter, 6)


def outside(row):
    row[5] += 1


assert_raises(IndexError, outside, [1])
assert_raises(TypeError, outside, (1, 2, 3, 4, 5, 6))
