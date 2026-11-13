# spec: PLS-315 27.1.4, 27.1.6, 27.1.8, 19.3.27
# description: enumerate, zip and map over an instance take each item from
# its class's Python __next__, which may call others, in order, also beside
# list iterators and in a for loop, a comprehension or a consumer; a
# StopIteration from it ends the adapter, a zip after taking the earlier
# iterables' items, and any other exception propagates; next() of such an
# adapter, also with a default, takes one item; inside functions as at
# module level.
from harness import *

log = []

class Counter:
    def __init__(self, n, tag="c"): self.n, self.tag = n, tag
    def __iter__(self): return self
    def __next__(self):
        log.append(self.tag + str(self.n))
        if self.n == 7: raise KeyError("k")
        if not self.n: raise StopIteration
        self.n -= 1
        return self.n

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def adapted():
    del log[:]
    out = [list(enumerate(Counter(2))), next(enumerate(Counter(1), 5)),
           list(zip(Counter(3, "a"), Counter(1, "b"))), list(zip([1, 2, 3], Counter(2))),
           list(map(abs, Counter(2))), list(map(lambda x, y: x * y, Counter(2), Counter(3, "d"))),
           dict(enumerate(Counter(1))), [k + v for k, v in enumerate(Counter(2))]]
    for k, v in zip("xy", Counter(1, "f")): out.append((k, v))
    out.append(error(lambda: list(enumerate(Counter(7)))))
    out.append(error(lambda: list(zip(Counter(1), Counter(7, "g")))))
    z = zip(Counter(2, "h"), Counter(1, "i"))
    out.append([next(z), next(z, "end"), next(z, "end")])
    out.append(list(log))
    return out

expected = [[(0, 1), (1, 0)], (5, 0), [(2, 0)], [(1, 1), (2, 0)], [1, 0], [2, 0], {0: 0}, [1, 1],
            ("x", 0), ("KeyError", "'k'"), ("KeyError", "'k'"), [(1, 0), "end", "end"],
            ["c2", "c1", "c0", "c1", "a3", "b1", "a2", "b0", "c2", "c1", "c0", "c2", "c1", "c0",
             "c2", "d3", "c1", "d2", "c0", "c1", "c0", "c2", "c1", "c0", "f1", "f0", "c7", "c1", "g7",
             "h2", "i1", "h1", "i0", "h0"]]
assert_eq(adapted(), expected)
assert_eq(adapted(), expected)
log.clear()
assert_eq([list(enumerate(Counter(1))), next(zip(Counter(1), Counter(0)), 9)], [[(0, 0)], 9])
assert_eq(log, ["c1", "c0", "c1", "c0"])
