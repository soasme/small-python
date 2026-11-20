# spec: PLS-315 27.1.4, 27.1.5, 27.1.6, 27.1.8
# description: enumerate(), filter(), map() and zip() over a zip, map or
# enumerate that mixes an instance iterator, whose Python __next__ may
# loop, with a generator, strict or not, take each item in order in
# list(), a loop, a yield from, a comprehension or next(): the generator's
# item reaches the adapter that asked for it, then each adapter around it;
# an iterable's end or error ends them all, a strict one's lengths checked.
from harness import *

log = []
def gen(name, *items, ret=None):
    for item in items:
        for _ in range(2): pass
        log.append((name, item)); yield item
    log.append((name, "end")); return ret
class It:
    def __init__(self, name, n): self.name = name; self.n = n
    def __iter__(self): return self
    def __next__(self):
        for _ in range(2): pass
        log.append((self.name, self.n))
        if self.n <= 0: raise StopIteration
        self.n -= 1; return self.n
def bad():
    yield 1
    raise KeyError("k")
def run(f):
    del log[:]
    try: r = f()
    except BaseException as e: r = (type(e).__name__, str(e))
    return r, list(log)
def loop(it):
    out = []
    for x in it: out.append(x)
    return out
def odd(x): log.append(("odd", x)); return x[0] % 2
def yf(it):
    r = yield from it
    log.append(("yf", r))
out = []
for make in [list, loop, lambda z: list(yf(z)), (lambda z: [x for x in z])]:
    for f in [
        lambda: enumerate(zip(It("i", 2), gen("a", 1, 2))),
        lambda: enumerate(zip(It("i", 3), gen("a", 1, 2))),
        lambda: enumerate(zip(It("i", 2), gen("a", 1, 2), strict=True)),
        lambda: enumerate(zip(It("i", 2), gen("a", 1), strict=True)),
        lambda: enumerate(zip(It("i", 1), gen("a", 1, 2), strict=True)),
        lambda: enumerate(zip(It("i", 2), bad())),
        lambda: filter(odd, zip(It("i", 3), gen("a", 1, 2, 3))),
        lambda: filter(None, zip(It("i", 2), gen("a", 1, 2))),
        lambda: zip(zip(It("i", 2), gen("a", 1, 2)), It("j", 3)),
        lambda: zip(It("j", 3), zip(It("i", 2), gen("a", 1, 2))),
        lambda: map(lambda p, q: (p, q), zip(It("i", 2), gen("a", 1, 2)), It("j", 3)),
        lambda: enumerate(enumerate(zip(It("i", 2), gen("a", 1, 2)))),
        lambda: enumerate(map(pow, It("i", 2), gen("a", 2, 3))),
        lambda: zip(enumerate(zip(It("i", 2), gen("a", 1, 2))), gen("b", 7, 8, 9)),
    ]:
        out.append(run(lambda: make(f())))
z = enumerate(zip(It("i", 2), gen("a", 1, 2, ret=5)))
out.append([run(lambda: next(z)) for _ in range(4)])
z = enumerate(zip(It("i", 2), gen("a", 1), strict=True))
out.append([run(lambda: next(z)) for _ in range(3)])

expected = [([(0, (1, 1)), (1, (0, 2))], [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0)]),
 ([(0, (2, 1)), (1, (1, 2))], [('i', 3), ('a', 1), ('i', 2), ('a', 2), ('i', 1), ('a', 'end')]),
 ([(0, (1, 1)), (1, (0, 2))], [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0), ('a', 'end')]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('i', 2), ('a', 1), ('i', 1), ('a', 'end')]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('i', 1), ('a', 1), ('i', 0), ('a', 2)]),
 (('KeyError', "'k'"), [('i', 2), ('i', 1)]),
 ([(1, 2)],
  [('i', 3),
   ('a', 1),
   ('odd', (2, 1)),
   ('i', 2),
   ('a', 2),
   ('odd', (1, 2)),
   ('i', 1),
   ('a', 3),
   ('odd', (0, 3)),
   ('i', 0)]),
 ([(1, 1), (0, 2)], [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0)]),
 ([((1, 1), 2), ((0, 2), 1)],
  [('i', 2), ('a', 1), ('j', 3), ('i', 1), ('a', 2), ('j', 2), ('i', 0)]),
 ([(2, (1, 1)), (1, (0, 2))],
  [('j', 3), ('i', 2), ('a', 1), ('j', 2), ('i', 1), ('a', 2), ('j', 1), ('i', 0)]),
 ([((1, 1), 2), ((0, 2), 1)],
  [('i', 2), ('a', 1), ('j', 3), ('i', 1), ('a', 2), ('j', 2), ('i', 0)]),
 ([(0, (0, (1, 1))), (1, (1, (0, 2)))], [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0)]),
 ([(0, 1), (1, 0)], [('i', 2), ('a', 2), ('i', 1), ('a', 3), ('i', 0)]),
 ([((0, (1, 1)), 7), ((1, (0, 2)), 8)],
  [('i', 2), ('a', 1), ('b', 7), ('i', 1), ('a', 2), ('b', 8), ('i', 0)]),
 ([(0, (1, 1)), (1, (0, 2))], [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0)]),
 ([(0, (2, 1)), (1, (1, 2))], [('i', 3), ('a', 1), ('i', 2), ('a', 2), ('i', 1), ('a', 'end')]),
 ([(0, (1, 1)), (1, (0, 2))], [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0), ('a', 'end')]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('i', 2), ('a', 1), ('i', 1), ('a', 'end')]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('i', 1), ('a', 1), ('i', 0), ('a', 2)]),
 (('KeyError', "'k'"), [('i', 2), ('i', 1)]),
 ([(1, 2)],
  [('i', 3),
   ('a', 1),
   ('odd', (2, 1)),
   ('i', 2),
   ('a', 2),
   ('odd', (1, 2)),
   ('i', 1),
   ('a', 3),
   ('odd', (0, 3)),
   ('i', 0)]),
 ([(1, 1), (0, 2)], [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0)]),
 ([((1, 1), 2), ((0, 2), 1)],
  [('i', 2), ('a', 1), ('j', 3), ('i', 1), ('a', 2), ('j', 2), ('i', 0)]),
 ([(2, (1, 1)), (1, (0, 2))],
  [('j', 3), ('i', 2), ('a', 1), ('j', 2), ('i', 1), ('a', 2), ('j', 1), ('i', 0)]),
 ([((1, 1), 2), ((0, 2), 1)],
  [('i', 2), ('a', 1), ('j', 3), ('i', 1), ('a', 2), ('j', 2), ('i', 0)]),
 ([(0, (0, (1, 1))), (1, (1, (0, 2)))], [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0)]),
 ([(0, 1), (1, 0)], [('i', 2), ('a', 2), ('i', 1), ('a', 3), ('i', 0)]),
 ([((0, (1, 1)), 7), ((1, (0, 2)), 8)],
  [('i', 2), ('a', 1), ('b', 7), ('i', 1), ('a', 2), ('b', 8), ('i', 0)]),
 ([(0, (1, 1)), (1, (0, 2))], [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0), ('yf', None)]),
 ([(0, (2, 1)), (1, (1, 2))],
  [('i', 3), ('a', 1), ('i', 2), ('a', 2), ('i', 1), ('a', 'end'), ('yf', None)]),
 ([(0, (1, 1)), (1, (0, 2))],
  [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0), ('a', 'end'), ('yf', None)]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('i', 2), ('a', 1), ('i', 1), ('a', 'end')]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('i', 1), ('a', 1), ('i', 0), ('a', 2)]),
 (('KeyError', "'k'"), [('i', 2), ('i', 1)]),
 ([(1, 2)],
  [('i', 3),
   ('a', 1),
   ('odd', (2, 1)),
   ('i', 2),
   ('a', 2),
   ('odd', (1, 2)),
   ('i', 1),
   ('a', 3),
   ('odd', (0, 3)),
   ('i', 0),
   ('yf', None)]),
 ([(1, 1), (0, 2)], [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0), ('yf', None)]),
 ([((1, 1), 2), ((0, 2), 1)],
  [('i', 2), ('a', 1), ('j', 3), ('i', 1), ('a', 2), ('j', 2), ('i', 0), ('yf', None)]),
 ([(2, (1, 1)), (1, (0, 2))],
  [('j', 3), ('i', 2), ('a', 1), ('j', 2), ('i', 1), ('a', 2), ('j', 1), ('i', 0), ('yf', None)]),
 ([((1, 1), 2), ((0, 2), 1)],
  [('i', 2), ('a', 1), ('j', 3), ('i', 1), ('a', 2), ('j', 2), ('i', 0), ('yf', None)]),
 ([(0, (0, (1, 1))), (1, (1, (0, 2)))],
  [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0), ('yf', None)]),
 ([(0, 1), (1, 0)], [('i', 2), ('a', 2), ('i', 1), ('a', 3), ('i', 0), ('yf', None)]),
 ([((0, (1, 1)), 7), ((1, (0, 2)), 8)],
  [('i', 2), ('a', 1), ('b', 7), ('i', 1), ('a', 2), ('b', 8), ('i', 0), ('yf', None)]),
 ([(0, (1, 1)), (1, (0, 2))], [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0)]),
 ([(0, (2, 1)), (1, (1, 2))], [('i', 3), ('a', 1), ('i', 2), ('a', 2), ('i', 1), ('a', 'end')]),
 ([(0, (1, 1)), (1, (0, 2))], [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0), ('a', 'end')]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('i', 2), ('a', 1), ('i', 1), ('a', 'end')]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('i', 1), ('a', 1), ('i', 0), ('a', 2)]),
 (('KeyError', "'k'"), [('i', 2), ('i', 1)]),
 ([(1, 2)],
  [('i', 3),
   ('a', 1),
   ('odd', (2, 1)),
   ('i', 2),
   ('a', 2),
   ('odd', (1, 2)),
   ('i', 1),
   ('a', 3),
   ('odd', (0, 3)),
   ('i', 0)]),
 ([(1, 1), (0, 2)], [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0)]),
 ([((1, 1), 2), ((0, 2), 1)],
  [('i', 2), ('a', 1), ('j', 3), ('i', 1), ('a', 2), ('j', 2), ('i', 0)]),
 ([(2, (1, 1)), (1, (0, 2))],
  [('j', 3), ('i', 2), ('a', 1), ('j', 2), ('i', 1), ('a', 2), ('j', 1), ('i', 0)]),
 ([((1, 1), 2), ((0, 2), 1)],
  [('i', 2), ('a', 1), ('j', 3), ('i', 1), ('a', 2), ('j', 2), ('i', 0)]),
 ([(0, (0, (1, 1))), (1, (1, (0, 2)))], [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0)]),
 ([(0, 1), (1, 0)], [('i', 2), ('a', 2), ('i', 1), ('a', 3), ('i', 0)]),
 ([((0, (1, 1)), 7), ((1, (0, 2)), 8)],
  [('i', 2), ('a', 1), ('b', 7), ('i', 1), ('a', 2), ('b', 8), ('i', 0)]),
 [((0, (1, 1)), [('i', 2), ('a', 1)]),
  ((1, (0, 2)), [('i', 1), ('a', 2)]),
  (('StopIteration', ''), [('i', 0)]),
  (('StopIteration', ''), [('i', 0)])],
 [((0, (1, 1)), [('i', 2), ('a', 1)]),
  (('ValueError', 'zip() argument 2 is shorter than argument 1'), [('i', 1), ('a', 'end')]),
  (('StopIteration', ''), [('i', 0)])]]
assert_eq(out, expected)
