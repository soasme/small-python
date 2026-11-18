# spec: PLS-315 27.1.4, 27.1.6, 27.1.8
# description: zip(), enumerate() and map() over another zip or enumerate
# of a map, or of an instance with a Python __getitem__, take each item as
# the inner adapter makes it, its calls, which may loop, in order: a loop,
# a consumer, dict(), sorted() and next() alike. An error from an inner
# map's function propagates through each adapter, the zips dropping the
# items they took; a StopIteration from it ends them all; the adapters go
# on with their next items after an error. Inside functions as at module
# level.
from harness import *

log = []
def spin():
    for _ in range(2): pass

class K:
    def __init__(self, v): self.v = v
    def __str__(self): spin(); log.append(self.v); return "k%d" % self.v

def f(x):
    spin(); log.append(("f", x))
    if x == 3: raise StopIteration
    if x == 4: raise ValueError("four")
    return x * 10

class G:
    def __init__(self, n): self.n = n
    def __getitem__(self, i):
        spin(); log.append(("g", i))
        if i >= self.n: raise IndexError
        return i

a, b, c = K(1), K(2), K(3)

def run(thunk):
    del log[:]
    try:
        r = thunk()
    except ValueError as e:
        r = str(e)
    return r, list(log)

def loop(it):
    out = []
    for x in it:
        log.append("x")
        out.append(x)
    return out

def results():
    out = [run(lambda: list(enumerate(zip(map(str, [a, b]), "xyz")))),
           run(lambda: loop(enumerate(zip(map(str, [a, b]), (7, 8, 9))))),
           run(lambda: list(zip(zip(map(f, [1, 2]), "ab"), map(str, [c, a, b])))),
           run(lambda: list(zip(zip(map(f, [1, 3, 5]), "abc"), "pq"))),
           run(lambda: loop(zip(enumerate(map(f, [1, 4, 5])), "abc"))),
           run(lambda: list(map(len, zip(map(str, [a]), map(f, [2]))))),
           run(lambda: list(zip(enumerate(zip(G(3), map(str, [a, b, c]))), "ab"))),
           run(lambda: dict(enumerate(zip(map(str, [b]), map(f, [1]))))),
           run(lambda: sum(x for x, _ in zip(map(f, [1, 2]), enumerate(map(str, [a, b]))))),
           run(lambda: list(enumerate(enumerate(enumerate(map(f, [1, 2])))))),
           run(lambda: sorted(zip(map(str, [b, a]), enumerate(map(f, [2, 1])))))]
    z = zip(zip("ab", map(f, [1, 4, 2])), "uvw")
    out += [run(lambda: next(z)), run(lambda: next(z)), run(lambda: list(z))]
    e = enumerate(zip(map(f, [4, 2]), "xy"))
    out += [run(lambda: list(e)), run(lambda: list(e))]
    return out

expected = [([(0, ("k1", "x")), (1, ("k2", "y"))], [1, 2]),
            ([(0, ("k1", 7)), (1, ("k2", 8))], [1, "x", 2, "x"]),
            ([((10, "a"), "k3"), ((20, "b"), "k1")], [("f", 1), 3, ("f", 2), 1]),
            ([((10, "a"), "p")], [("f", 1), ("f", 3)]),
            ("four", [("f", 1), "x", ("f", 4)]),
            ([2], [1, ("f", 2)]),
            ([((0, (0, "k1")), "a"), ((1, (1, "k2")), "b")], [("g", 0), 1, ("g", 1), 2, ("g", 2), 3]),
            ({0: ("k2", 10)}, [2, ("f", 1)]),
            (30, [("f", 1), 1, ("f", 2), 2]),
            ([(0, (0, (0, 10))), (1, (1, (1, 20)))], [("f", 1), ("f", 2)]),
            ([("k1", (1, 10)), ("k2", (0, 20))], [2, ("f", 2), 1, ("f", 1)]),
            ((("a", 10), "u"), [("f", 1)]), ("four", [("f", 4)]), ([], []),
            ("four", [("f", 4)]), ([(0, (20, "x"))], [("f", 2)])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
