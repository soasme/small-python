# spec: PLS-315 27.1.1, 27.1.4, 27.1.5, 27.1.6, 27.1.8, 7.7.1
# description: zip, map, enumerate and filter call each instance
# iterable's Python __iter__, which may call others, once, left to right,
# when created, beside lists and with a function first; an enumerate
# converts its start first; an __iter__ that raises or returns a
# non-iterator stops those after it, and an argument error comes first;
# a subclass of zip or enumerate does the same; inside functions as at
# module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class It:
    def __init__(self, *v): self.v = v
    def __iter__(self):
        spin(); log.append(self.v)
        if self.v == ("bad",): return 5
        if self.v == ("err",): raise KeyError("k")
        return iter(self.v)

class Index:
    def __index__(self): log.append("index"); return 7

class Z(zip): pass
class E(enumerate):
    def __init__(self, *a): log.append("init")

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def created():
    del log[:]
    out = [list(zip(It(1, 2), [3, 4], It(5, 6))), list(map(lambda a, b: a + b, It(1), It(10))),
           list(enumerate(It("a", "b"))), list(enumerate(It("c"), Index())), list(filter(None, It(0, 1)))]
    a, b = It(8), It(9)
    out.append([list(zip(a, b)), list(zip([0], a)), list(map(str, a)), list(enumerate(a, 1)), list(filter(None, b))])
    out.append(error(lambda: zip(It(1), It("bad"), It(2))))
    out.append(error(lambda: map(len, [1], It("err"), It(3))))
    out.append(error(lambda: zip(It(1), 5, It(2))))
    out.append(error(lambda: enumerate(It("x"), "s")))
    out.append(error(lambda: filter(It(1))))
    z, e = Z(It(4), It(5)), E(It(6))
    out.append([type(z).__name__, list(z), type(e).__name__, list(e)])
    out.append(list(log))
    return out

expected = [[(1, 3, 5), (2, 4, 6)], [11], [(0, "a"), (1, "b")], [(7, "c")], [1],
            [[(8, 9)], [(0, 8)], ["8"], [(1, 8)], [9]],
            ("TypeError", "It.__iter__() must return an iterator, not int"), ("KeyError", "'k'"),
            ("TypeError", "'int' object is not iterable"),
            ("TypeError", "'str' object cannot be interpreted as an integer"),
            ("TypeError", "filter expected 2 arguments, got 1"),
            ["Z", [(4, 5)], "E", [(0, 6)]],
            [(1, 2), (5, 6), (1,), (10,), ("a", "b"), "index", ("c",), (0, 1),
             (8,), (9,), (8,), (8,), (8,), (9,), (1,), ("bad",), ("err",), (1,), (4,), (5,), (6,), "init"]]
assert_eq(created(), expected)
assert_eq(created(), expected)
log.clear()
assert_eq([list(zip(It(1), It(2))), list(enumerate(It(3), 1))], [[(1, 2)], [(1, 3)]])
assert_eq(log, [(1,), (2,), (3,)])
