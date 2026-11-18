# spec: PLS-315 19.3.26, 7.2.4, 7.2.5
# description: min() and max() of a generator, of a map, or of an
# instance whose Python __iter__ returns the iterator, compare each item
# as it arrives with the best so far by the item's Python __lt__ or
# __gt__, which may loop; after its NotImplemented the best's reflected
# method decides, a result's __bool__ is called, an exception propagates,
# an empty source raises ValueError or gives the default. Inside functions
# as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class V:
    def __init__(self, n): self.n = n
    def __gt__(self, o): spin(); log.append((">", self.n, o.n)); return self.n > o.n
    def __lt__(self, o): spin(); log.append(("<", self.n, o.n)); return self.n < o.n

class N:
    def __init__(self, n): self.n = n
    def __gt__(self, o): log.append("Ngt"); return NotImplemented
    def __lt__(self, o): log.append(("Nlt", self.n)); return True

class T:
    def __bool__(self): spin(); log.append("bool"); return True

class B:
    def __init__(self, n): self.n = n
    def __gt__(self, o): return T()

class It:
    def __iter__(self): spin(); log.append("iter"); return iter([V(2), V(5), V(1)])

class Bad:
    def __gt__(self, o): raise KeyError("gt")

def gen(*xs):
    for x in xs:
        spin(); log.append("g"); yield x

def run(f):
    del log[:]
    try:
        r = f()
    except Exception as e:
        r = (type(e).__name__, str(e))
    return r, list(log)

def results():
    return [run(lambda: max(gen(V(1), V(3), V(2))).n), run(lambda: min(gen(V(1), V(3), V(0))).n),
            run(lambda: max(It()).n), run(lambda: min(It()).n), run(lambda: max(gen())), run(lambda: min(gen(), default=7)),
            run(lambda: max(gen(N(1), N(2))).n), run(lambda: max(gen(B(1), B(2))).n), run(lambda: max(gen(Bad(), Bad()))),
            run(lambda: max(gen(1, "a"))), run(lambda: max(map(V, gen(1, 2))).n)]

expected = [(3, ["g", "g", (">", 3, 1), "g", (">", 2, 3)]), (0, ["g", "g", ("<", 3, 1), "g", ("<", 0, 1)]),
            (5, ["iter", (">", 5, 2), (">", 1, 5)]), (1, ["iter", ("<", 5, 2), ("<", 1, 2)]),
            (("ValueError", "max() iterable argument is empty"), []), (7, []),
            (2, ["g", "g", "Ngt", ("Nlt", 1)]), (2, ["g", "g", "bool"]), (("KeyError", "'gt'"), ["g", "g"]),
            (("TypeError", "'>' not supported between instances of 'str' and 'int'"), ["g", "g"]),
            (2, ["g", "g", (">", 2, 1)])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
