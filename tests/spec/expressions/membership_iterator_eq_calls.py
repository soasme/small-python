# spec: PLS-315 7.8.3, 13.10
# description: x in a generator, an instance with a Python __iter__, or
# one with only a Python __getitem__, compares each item v with x as
# v == x, in order: v's __eq__, which may loop, or x's first when x's class
# derives from v's or v has none; a NotImplemented calls the other's, then
# a builtin base's comparison or identity decides; the first true result
# stops the search, leaving the rest of a generator, and an exception
# propagates. __getitem__ is called with 0, 1, ... until IndexError.
# Inside functions as at module level.
from harness import *

log = []
def gen(*items):
    for item in items: yield item
class Key:
    def __init__(self, n): self.n = n
    def __eq__(self, other):
        for _ in (): pass
        log.append(("eq", self.n, type(other).__name__))
        return self.n == other
    __hash__ = None
class Sub(Key):
    def __eq__(self, other):
        for _ in (): pass
        log.append(("sub", self.n))
        return NotImplemented
class Declines:
    def __eq__(self, other):
        for _ in (): pass
        log.append("declines")
        return NotImplemented
class IntKey(int):
    def __eq__(self, other):
        for _ in (): pass
        log.append(("intkey", int(self)))
        return NotImplemented
    __hash__ = int.__hash__
class Truth:
    def __init__(self, t): self.t = t
    def __bool__(self): return self.t
class Odd:
    def __eq__(self, other): return Truth(False)
class Raises:
    def __eq__(self, other):
        for _ in (): pass
        raise KeyError("eq")
def searches():
    del log[:]
    out = [3 in gen(Key(1), Key(3), Key(5)), list(log)]
    del log[:]
    k = Key(2)
    out += [Key(2) in gen(1, 2), Sub(2) in gen(Key(2)), k in gen(k), list(log)]
    del log[:]
    out += [3 in gen(IntKey(3)), Declines() in gen(Declines()), 4 not in gen(Odd()), list(log)]
    try: 1 in gen(Raises())
    except KeyError as e: out.append(str(e))
    g = gen(Key(1), Key(2), Key(3))
    out += [2 in g, [x.n for x in g]]
    return out

class Seq:
    def __init__(self, items, error=IndexError): self.items, self.error = items, error
    def __getitem__(self, i):
        for _ in (): pass
        log.append(i)
        if i >= len(self.items): raise self.error(i)
        return self.items[i]
def sequences():
    del log[:]
    out = [2 in Seq([1, 2, 3]), 5 in Seq([1, 2]), 5 not in Seq([]), 3 in Seq([Key(1), Key(3)]), list(log)]
    del log[:]
    for bad in (Seq([1], KeyError), Seq([1], StopIteration)):
        try: out.append(9 in bad)
        except KeyError as e: out.append(("KeyError", str(e)))
    out.append(list(log))
    tests = []
    if 2 in Seq([2]): tests.append("in")
    while 4 not in Seq([4]): break
    else: tests.append("never")
    out.append(tests)
    return out

expected = ([True, [('eq', 1, 'int'), ('eq', 3, 'int')], True, False, True, [('eq', 2, 'int'), ('eq', 2, 'int'), ('sub', 2), ('eq', 2, 'Sub'), ('sub', 2)], True, False, True, [('intkey', 3), 'declines', 'declines'], "'eq'", True, [3]], [True, False, True, True, [0, 1, 0, 1, 2, 0, 0, ('eq', 1, 'int'), 1, ('eq', 3, 'int')], ('KeyError', '1'), False, [0, 1, 0, 1], ['in', 'never']])
assert_eq((searches(), sequences()), expected)

def nested():
    return searches(), sequences()

assert_eq(nested(), expected)
