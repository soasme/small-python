# spec: PLS-315 13.6, 13.7, 13.10, 14.2, 14.3
# description: An assignment of nested arithmetic, unary operators and
# comparisons on names, literals and items evaluates its operands left to
# right, each once, calls each special method once, and stores the result
# into a name or an item, when operands change from numbers to objects.
from harness import *

calls = []


class Logged:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __mul__(self, other):
        calls.append(self.name + "*")
        return Logged(self.name, self.value * other)

    def __rmul__(self, other):
        calls.append("*" + self.name)
        return Logged(self.name, other * self.value)

    def __add__(self, other):
        calls.append(self.name + "+")
        other = other.value if isinstance(other, Logged) else other
        return Logged(self.name, self.value + other)

    def __neg__(self):
        calls.append("-" + self.name)
        return Logged(self.name, -self.value)

    def __lt__(self, other):
        calls.append(self.name + "<")
        return self.value < other

    def __isub__(self, other):
        calls.append(self.name + "-=")
        self.value -= other.value if isinstance(other, Logged) else other
        return self


class Row(list):
    def __getitem__(self, key):
        calls.append(("get", key))
        return list.__getitem__(self, key)

    def __setitem__(self, key, value):
        calls.append(("set", key))
        list.__setitem__(self, key, value)


def physics(dx, dy, dt, row):
    d2 = dx * dx + dy * dy
    mag = dt / (d2 * d2 ** 0.5)
    row[0] = -dx * mag
    row[1] -= dy * mag * 2
    nearer = d2 * 2 < dt + 1
    ordered = 0 <= dx * 2 < dy + 10
    return d2, mag, row, nearer, ordered


assert_same(physics(3, 4, 250, [0, 1]), (25, 2.0, [-6.0, -15.0], True, True))
assert_same(physics(0.5, 0.5, 1.0, [0.0, 0.0])[3], True)

a = Logged("a", 2)
b = Logged("b", 3)
result = a * 2 + b * 3
assert_same(result.value, 13)
assert_same(calls, ["a*", "b*", "a+"])
del calls[:]
result = -a * 2
assert_same(result.value, -4)
assert_same(calls, ["-a", "a*"])
del calls[:]
result = 2 * a + 1
assert_same(result.value, 5)
assert_same(calls, ["*a", "a+"])
del calls[:]
nearer = a * 2 < 5
assert_same(nearer, True)
assert_same(calls, ["a*", "a<"])
del calls[:]
held = a
held -= b * 2
assert_same(held is a and a.value, -4)
assert_same(calls, ["b*", "a-="])
del calls[:]

row = Row([1, 2])
total = row[0] * 2 + row[1] * 3
assert_same(total, 8)
assert_same(calls, [("get", 0), ("get", 1)])
del calls[:]
row[1] = row[0] * 2 + 1
assert_same(calls, [("get", 0), ("set", 1)])
assert_same(list(row), [1, 3])
del calls[:]


def changing(values):
    out = 0
    for value in values:
        out = value * 2 + value * 3
    return out


assert_same(changing([1, 2]), 10)
assert_same(changing([1, 2.0]), 10.0)
assert_same(changing([1, "a"]), "aaaaa")
assert_raises(TypeError, changing, [1, None])


def missing():
    value = 1 * 2 + absent * 3
    return value


assert_raises(NameError, missing)


def divided(x):
    value = x * 2 + 1 // (x - x)
    return value


assert_raises(ZeroDivisionError, divided, 1)
