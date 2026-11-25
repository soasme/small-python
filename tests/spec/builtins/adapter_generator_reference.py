# spec: PLS-315 27.1.4, 27.1.5, 27.1.8, 13.16.3
# description: enumerate(), filter() and zip(), strict or not, over a
# generator, an empty one, an instance iterator whose Python __next__
# loops, or one another, taken by list(), a for loop, a comprehension, next() or a
# (nested) yield from, ask each iterable in the order the equivalent
# Python iterators do and give the same items, end and error.
from harness import *

log = []
def gen(name, *items):
    for item in items:
        for _ in range(2): pass
        log.append((name, item)); yield item
    log.append((name, "end"))
def bad():
    yield 1
    raise KeyError("k")
class It:
    def __init__(self, name, n): self.name = name; self.n = n
    def __iter__(self): return self
    def __next__(self):
        for _ in range(2): pass
        log.append((self.name, self.n))
        if self.n <= 0: raise StopIteration
        self.n -= 1; return self.n
def odd(x):
    log.append(("odd", x))
    return (x[-1] if isinstance(x, tuple) else x) % 2

# The Python iterators each builtin is equivalent to: each next() asks
# its iterables again, even after one ended.
class py_enumerate:
    def __init__(self, it): self.it = iter(it); self.n = 0
    def __iter__(self): return self
    def __next__(self):
        x = next(self.it)
        self.n += 1
        return self.n - 1, x
class py_filter:
    def __init__(self, f, it): self.f = f; self.it = iter(it)
    def __iter__(self): return self
    def __next__(self):
        while True:
            x = next(self.it)
            if (bool(x) if self.f is None else self.f(x)): return x
def ordinal(k): return f"s 1-{k}" if k > 1 else " 1"
class py_zip:
    def __init__(self, *its, strict=False): self.its = [iter(i) for i in its]; self.strict = strict
    def __iter__(self): return self
    def __next__(self):
        items = []
        for k, i in enumerate(self.its):
            try:
                items.append(next(i))
            except StopIteration:
                if not self.strict: raise
                if k: raise ValueError(f"zip() argument {k + 1} is shorter than argument{ordinal(k)}") from None
                for j, rest in enumerate(self.its[1:], 2):
                    try: next(rest)
                    except StopIteration: continue
                    raise ValueError(f"zip() argument {j} is longer than argument{ordinal(j - 1)}")
                raise
        return tuple(items)

def wraps(e, f, z):
    return [lambda x: e(x), lambda x: f(odd, x), lambda x: f(None, x), lambda x: z(x, It("j", 3)),
            lambda x: z(It("j", 3), x), lambda x: z(x, gen("c", 5, 6, 7), strict=True), lambda x: z(x)]
builtin = wraps(enumerate, filter, zip)
python = wraps(py_enumerate, py_filter, py_zip)
leaves = [lambda: gen("a", 1, 2, 3), lambda: It("i", 3), lambda: [7, 8], bad, lambda: gen("e")]
def yf(it):
    r = yield from it
    log.append(("yf", r))
def loop(it):
    out = []
    for x in it: out.append(x)
    return out
def nexts(it):
    return [next(it, "done") for _ in range(5)]
makes = [list, loop, lambda z: [x for x in z], nexts, lambda z: list(yf(z)), lambda z: list(yf(yf(z)))]
def run(make, f):
    del log[:]
    try: r = make(f())
    except Exception as e: r = (type(e).__name__, str(e))
    return r, list(log)

checked = 0
for leaf in leaves:
    for i in range(len(builtin)):
        for j in [None] + list(range(len(builtin))):
            for make in makes:
                b = (lambda: builtin[j](builtin[i](leaf()))) if j is not None else (lambda: builtin[i](leaf()))
                p = (lambda: python[j](python[i](leaf()))) if j is not None else (lambda: python[i](leaf()))
                assert_eq(run(make, b), run(make, p))
                checked += 1
assert_eq(checked, 5 * 7 * 8 * 6)
