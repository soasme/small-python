# spec: PLS-315 14.2.2
# description: Tuple, list, starred, and chained assignment targets; a
# subscript among them stores through its __setitem__ in target order.
x = 1
assert x == 1

x = 1, 2, 3
assert x == (1, 2, 3)

x, y = 1, 2
assert x == 1
assert y == 2

x, y = (y, x)

assert x == 2
assert y == 1

((x, y), z) = ((1, 2), 3)

assert (x, y, z) == (1, 2, 3)

q = (1, 2, 3)
(x, y, z) = q
assert y == q[1]

x = (a, b, c) = y = q

assert (a, b, c) == q
assert x == q
assert y == q

a, *b = q
print(a)
print(b)
assert a == 1
assert b == [2, 3]

a, *b, c, d = q
print(a)
print(b)
assert a == 1
assert b == []
assert c == 2
assert d == 3

a, = [1]
assert a == 1

def g():
    yield 1337
    yield 42

a, b = g()
assert a == 1337
assert b == 42

# Variable annotations:
a: bool
b: bool = False

assert a == 1337
assert b == False

# PEP 649: In Python 3.14, __annotations__ is not automatically defined at module level
# Accessing it raises NameError
from harness import *

with assert_raises(NameError):
    __annotations__

# Use __annotate__ to get annotations (PEP 649)
assert callable(__annotate__)
annotations = __annotate__(1)  # 1 = FORMAT_VALUE
assert annotations['a'] == bool
assert annotations['b'] == bool

n = 0

def a():
    global n
    n += 1
    return [0]

a()[0] += 1

assert n == 1

# Subscripts inside target lists, nested and starred, store left to right
# after the value is unpacked, each through the object's __setitem__.
stores = []
class Store:
    def __init__(self): self.items = {}
    def __setitem__(self, key, value):
        for _ in range(2): pass
        stores.append((key, value))
        self.items[key] = value
def targets():
    s, rows = Store(), [Store()]
    first, s["a"], (rows[0][1], *s["rest"]) = 1, 2, (3, 4, 5)
    rows[0][2] = s
    return first, s.items, rows[0].items[1], rows[0].items[2] is s
assert targets() == (1, {"a": 2, "rest": [4, 5]}, 3, True)
assert [key for key, _ in stores] == ["a", 1, "rest", 2], stores

# Unpacking a generator takes one item past the targets at most, and a
# star takes the rest; too few or too many raise ValueError.
taken = []
def numbers(n):
    for i in range(n):
        taken.append(i)
        yield i
def unpacked():
    results = []
    a, b = numbers(2)
    first, *rest = numbers(4)
    results.append((a, b, first, rest))
    for target in ("pair", "triple", "star"):
        try:
            if target == "pair": x, y = numbers(5)
            elif target == "triple": x, y, z = numbers(2)
            else: x, *y, z = numbers(1)
        except ValueError as e:
            results.append(str(e))
    return results
assert unpacked() == [(0, 1, 0, [1, 2, 3]), "too many values to unpack (expected 2)",
                      "not enough values to unpack (expected 3, got 2)",
                      "not enough values to unpack (expected at least 2, got 1)"]
assert taken == [0, 1, 0, 1, 2, 3, 0, 1, 2, 0, 1, 0], taken
