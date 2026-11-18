# spec: PLS-315 13.16.3, 27.1.4, 27.1.6, 27.1.8
# description: yield from a zip, enumerate or map that takes the items of
# a map, of a callable iterator or of a __getitem__ sequence yields each
# item as the adapter makes it, its calls, which may loop, in order: a
# map's function, an item's __str__ or __init__ conversion, a sentinel's
# __eq__. A StopIteration from a map's function ends the adapter, its
# value the yield from's; another error propagates at the yield from; a
# throw or close into the generator leaves the adapter's next items. Inside
# functions as at module level.
from harness import *

log = []
def spin():
    for _ in range(2): pass

class K:
    def __init__(self, v): self.v = v
    def __str__(self): spin(); log.append(self.v); return "k%d" % self.v
    def __eq__(self, o): spin(); log.append(("eq", self.v)); return isinstance(o, K) and o.v == self.v
    __hash__ = object.__hash__

def f(x):
    spin(); log.append(("f", x))
    if x == 3: raise StopIteration(33)
    if x == 4: raise ValueError("four")
    return x * 10

class G:
    def __init__(self, n): self.n = n
    def __getitem__(self, i):
        spin(); log.append(("g", i))
        if i >= self.n: raise IndexError
        return i

class P:
    def __init__(self, a): spin(); log.append(("P", a)); self.a = a

count = [0]
def tick():
    spin(); count[0] += 1; log.append(("t", count[0])); return K(count[0])

def gen(it):
    r = yield from it
    log.append(("ret", r))
    yield "end"

def run(thunk):
    del log[:]
    try:
        r = thunk()
    except ValueError as e:
        r = str(e)
    return r, list(log)

def thrown():
    g = gen(zip(map(f, [1, 2]), "ab"))
    out = [next(g)]
    try:
        g.throw(KeyError("k"))
    except KeyError as e:
        out.append(str(e))
    return out + [list(g)]

def closed():
    g = gen(enumerate(map(f, [1, 2])))
    out = [next(g)]
    g.close()
    return out

def results():
    count[0] = 0
    return [run(lambda: list(gen(zip("q", map(str, [K(2)]))))),
            run(lambda: list(gen(enumerate(map(f, [1, 2]))))),
            run(lambda: list(gen(zip(map(f, [1, 3, 5]), "abc")))),
            run(lambda: list(gen(zip(map(f, [1, 4]), "ab")))),
            run(lambda: list(gen(zip(G(2), map(str, [K(5), K(6), K(7)]))))),
            run(lambda: [(t.v, s) for t, s in list(gen(zip(iter(tick, K(3)), "abcd")))[:-1]]),
            run(lambda: list(gen(map(len, map(str, [K(1), K(22)]))))),
            run(lambda: [(p.a, s) for p, s in list(gen(zip(map(P, [1, 2]), "xy")))[:-1]]),
            run(lambda: list(gen(enumerate(zip(map(f, [1, 2]), map(str, [K(8), K(9)])))))),
            run(lambda: list(gen(zip("abc", map(f, [1, 2]), G(5))))),
            run(thrown), run(closed)]

expected = [([("q", "k2"), "end"], [2, ("ret", None)]),
            ([(0, 10), (1, 20), "end"], [("f", 1), ("f", 2), ("ret", None)]),
            ([(10, "a"), "end"], [("f", 1), ("f", 3), ("ret", 33)]),
            ("four", [("f", 1), ("f", 4)]),
            ([(0, "k5"), (1, "k6"), "end"], [("g", 0), 5, ("g", 1), 6, ("g", 2), ("ret", None)]),
            ([(1, "a"), (2, "b")], [("t", 1), ("eq", 3), ("t", 2), ("eq", 3), ("t", 3), ("eq", 3), ("ret", None)]),
            ([2, 3, "end"], [1, 22, ("ret", None)]),
            ([(1, "x"), (2, "y")], [("P", 1), ("P", 2), ("ret", None)]),
            ([(0, (10, "k8")), (1, (20, "k9")), "end"], [("f", 1), 8, ("f", 2), 9, ("ret", None)]),
            ([("a", 10, 0), ("b", 20, 1), "end"], [("f", 1), ("g", 0), ("f", 2), ("g", 1), ("ret", None)]),
            ([(10, "a"), "'k'", []], [("f", 1)]),
            ([(0, 10)], [("f", 1)])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
