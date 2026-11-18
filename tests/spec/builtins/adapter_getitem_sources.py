# spec: PLS-315 27.1.4, 27.1.6, 27.1.7, 27.1.8
# description: zip(), enumerate() and map() over an instance with only a
# Python __getitem__, or over reversed() of an instance with __len__ and
# a Python __getitem__, read its items by index as they go, the method
# looping; its IndexError ends that iterable and so the adapter, which
# then stays exhausted, a zip dropping the items it took of the others
# and asking them again on its next call, while another exception propagates and the same
# index is read again by the next call. dict(), list() and unpacking take
# such an adapter's items. Inside functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Seq:
    def __init__(self, n): self.n = n
    def __getitem__(self, i):
        spin(); log.append(i)
        if i >= self.n: raise IndexError(i)
        return i * 10

class Back:
    def __len__(self): return 2
    def __getitem__(self, i):
        spin(); log.append(("back", i))
        return "b%d" % i

class Flaky:
    def __init__(self): self.failed = False
    def __getitem__(self, i):
        spin(); log.append(("flaky", i))
        if i == 1 and not self.failed:
            self.failed = True
            raise KeyError(i)
        if i >= 3: raise IndexError(i)
        return i

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def adapters():
    del log[:]
    out = [list(zip("abcd", Seq(3))), dict(zip("ab", Seq(5))), list(enumerate(Seq(2))), list(map(lambda x: x + 1, Seq(2))),
           list(zip(Seq(3), reversed(Back())))]
    a, b = zip(Seq(2), Seq(2))
    out.append((a, b))
    it = zip(Seq(1))
    out += [next(it), list(it), list(it)]
    flaky = zip(Flaky())
    out += [next(flaky), error(lambda: next(flaky)), next(flaky), list(flaky)]
    again = zip(Seq(3), reversed(Back()))
    out += [list(again), list(again)]
    out.append(list(log))
    return out

expected = [[("a", 0), ("b", 10), ("c", 20)], {"a": 0, "b": 10}, [(0, 0), (1, 10)], [1, 11], [(0, "b1"), (10, "b0")],
            ((0, 0), (10, 10)), (0,), [], [], (0,), ("KeyError", "1"), (1,), [(2,)], [(0, "b1"), (10, "b0")], [],
            [0, 1, 2, 3, 0, 1, 0, 1, 2, 0, 1, 2, 0, ("back", 1), 1, ("back", 0), 2, 0, 0, 1, 1, 2, 0, 1,
             ("flaky", 0), ("flaky", 1), ("flaky", 1), ("flaky", 2), ("flaky", 3),
             0, ("back", 1), 1, ("back", 0), 2, 3]]

def main():
    return adapters()

assert_eq(main(), expected)
assert_eq(adapters(), expected)
