# spec: PLS-315 14.2, 7.7.1
# description: unpacking an instance with only a Python __getitem__ reads
# items 0, 1, ... by it, which may loop, until IndexError, and unpacking a
# map() or filter() of a Python function takes each item from it as it
# goes; too many or too few items raise ValueError after the items read,
# a starred target gathers the rest, and another exception from
# __getitem__ or the function propagates. Inside functions as at module
# level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Seq:
    def __init__(self, n, bad=None): self.n = n; self.bad = bad
    def __getitem__(self, i):
        spin(); log.append(i)
        if i == self.bad: raise KeyError(i)
        if i >= self.n: raise IndexError(i)
        return i * 10

def double(x):
    spin(); log.append(("f", x))
    if x == 9: raise LookupError(x)
    return x * 2

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def unpack3(v):
    a, b, c = v
    return a, b, c

def unpack_star(v):
    a, *b = v
    return a, b

def unpacks():
    del log[:]
    out = [unpack3(Seq(3)), unpack_star(Seq(3)), error(lambda: unpack3(Seq(4))), error(lambda: unpack3(Seq(2))),
           error(lambda: unpack3(Seq(5, bad=1))), error(lambda: unpack_star(Seq(0)))]
    out += [unpack3(map(double, [1, 2, 3])), unpack_star(filter(lambda x: (spin(), x)[1], [0, 1, 2, 3])),
            error(lambda: unpack3(map(double, [1, 9, 3]))), error(lambda: unpack3(map(double, [1, 2])))]
    out.append(list(log))
    return out

expected = [(0, 10, 20), (0, [10, 20]), ("ValueError", "too many values to unpack (expected 3)"),
            ("ValueError", "not enough values to unpack (expected 3, got 2)"), ("KeyError", "1"),
            ("ValueError", "not enough values to unpack (expected at least 1, got 0)"),
            (2, 4, 6), (1, [2, 3]), ("LookupError", "9"), ("ValueError", "not enough values to unpack (expected 3, got 2)"),
            [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 0, 1, 0,
             ("f", 1), ("f", 2), ("f", 3), ("f", 1), ("f", 9), ("f", 1), ("f", 2)]]

def main():
    return unpacks()

assert_eq(main(), expected)
assert_eq(unpacks(), expected)
for x, y in [Seq(2)]:
    assert_eq((x, y), (0, 10))
