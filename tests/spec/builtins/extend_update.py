# spec: PLS-315 25.1.3, 26.1.3, 26.1.1
# description: list.extend() and dict.update() of a generator or another
# lazy iterator take its items one at a time, each appended or stored
# before the next is made, so that the generator sees the object grow,
# inside functions as at module level; both return None. dict.update()
# stores pairs as dict() does, with the same errors, keeping the pairs
# before a failure, and treats an object with keys() as a mapping.
from harness import *

def spin():
    for _ in range(2): pass

def grow(target, n):
    for i in range(n):
        spin()
        yield len(target)

def pairs(target, n):
    for i in range(n):
        spin()
        yield i, len(target)

def failing(target):
    yield ("a", 1)
    spin()
    raise KeyError("stop")

class Count:
    def __init__(self, n): self.i, self.n = 0, n
    def __iter__(self): return self
    def __next__(self):
        spin()
        if self.i == self.n: raise StopIteration
        self.i += 1
        return self.i

class Mapping:
    def keys(self): return ["k"]
    def __getitem__(self, key): return key * 2
    def __iter__(self): return iter([("wrong", 0)])

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    xs = [9]
    out = [xs.extend(grow(xs, 3)), list(xs)]
    xs.extend(map(lambda v: v * 10, grow(xs, 2)))
    xs.extend(Count(2))
    xs.extend(zip(grow(xs, 1), grow([], 1)))
    out.append(xs)
    d = {"x": 0}
    out += [d.update(pairs(d, 3)), d]
    out.append(error(lambda: d.update((v for v in [(1, 2, 3)]))))
    out.append(error(lambda: d.update((v for v in [5]))))
    f = {}
    out += [error(lambda: f.update(failing(f))), f]
    m = {}
    m.update(Mapping())
    out.append(m)
    return out

expected = [None, [9, 1, 2, 3], [9, 1, 2, 3, 40, 50, 1, 2, (8, 0)],
            None, {"x": 0, 0: 1, 1: 2, 2: 3},
            ("ValueError", "dictionary update sequence element #0 has length 3; 2 is required"),
            ("TypeError", "object is not iterable"),
            ("KeyError", "'stop'"), {"a": 1}, {"k": "kk"}]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
