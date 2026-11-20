# spec: PLS-315 27.1.8, 27.1.6
# description: zip(strict=True) and map(strict=True) over instance
# iterators whose Python __next__ may loop, alone or mixed with
# generators, __getitem__ iterators and lists, take each item in order in
# list(), tuple(), a loop, dict() or next(); when the first ends, each
# later one is asked once in turn, a StopIteration from its __next__ ending
# it, an item making it longer; a later one ending first is shorter, and an
# error propagates. A zip that is not strict mixes them the same way.
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
class Bad:
    def __iter__(self): return self
    def __next__(self): raise KeyError("bad")
class Seq:
    def __init__(self, n): self.n = n
    def __getitem__(self, i):
        for _ in (): pass
        log.append(("seq", i))
        if i >= self.n: raise IndexError
        return i
def run(f):
    del log[:]
    try: r = f()
    except BaseException as e: r = (type(e).__name__, str(e))
    return r, list(log)
def loop(it):
    out = []
    for x in it: out.append(x)
    return out
out = []
for make in [list, tuple, loop, lambda z: dict((a, b) for a, b, *_ in z)]:
  cases = [
    lambda: zip(gen("a", 1), It("i", 1), gen("c", 5), strict=True),
    lambda: zip(gen("a", 1), It("i", 2), strict=True),
    lambda: zip(gen("a", 1, 2), It("i", 1), strict=True),
    lambda: zip(It("i", 2), gen("a", 1, 2), strict=True),
    lambda: zip(It("i", 1), gen("a", 1, 2), strict=True),
    lambda: zip(It("i", 2), gen("a", 1), strict=True),
    lambda: zip(It("i", 1), It("j", 1), strict=True),
    lambda: zip(It("i", 1), It("j", 2), strict=True),
    lambda: zip(It("i", 2), It("j", 1), strict=True),
    lambda: zip(It("i", 0), [1], It("j", 0), strict=True),
    lambda: zip(It("i", 0), [], It("j", 1), strict=True),
    lambda: zip(It("i", 1), Bad(), strict=True),
    lambda: zip(It("i", 0), Bad(), strict=True),
    lambda: zip(gen("a"), Bad(), strict=True),
    lambda: zip(It("i", 2), iter(Seq(2)), strict=True),
    lambda: zip(iter(Seq(1)), It("i", 2), strict=True),
    lambda: zip(gen("a", 1), It("i", 1), gen("c", 5)),
    lambda: zip(It("i", 3), gen("c", 5)),
    lambda: map(pow, It("i", 2), gen("a", 2, 3), strict=True),
    lambda: map(pow, It("i", 1), gen("a", 2, 3), strict=True),
    lambda: map(pow, gen("a", 2), It("i", 1), It("j", 2), strict=True),
    lambda: zip(zip(It("i", 2), It("j", 1), strict=True), [1, 2]),
  ]
  for f in cases: out.append(run(lambda: make(f())))
z = zip(gen("a", 1), It("i", 2), strict=True)
out.append(([run(lambda: next(z)) for _ in range(3)], run(lambda: next(z, "d"))))
z = zip(It("i", 1), gen("b", 3, 4), strict=True)
out.append([run(lambda: next(z)) for _ in range(3)])
z = zip(It("i", 1), It("j", 2), strict=True)
out.append([run(lambda: next(z)) for _ in range(3)])

expected = [([(1, 0, 5)], [('a', 1), ('i', 1), ('c', 5), ('a', 'end'), ('i', 0), ('c', 'end')]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('a', 1), ('i', 2), ('a', 'end'), ('i', 1)]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('a', 1), ('i', 1), ('a', 2), ('i', 0)]),
 ([(1, 1), (0, 2)], [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0), ('a', 'end')]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('i', 1), ('a', 1), ('i', 0), ('a', 2)]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('i', 2), ('a', 1), ('i', 1), ('a', 'end')]),
 ([(0, 0)], [('i', 1), ('j', 1), ('i', 0), ('j', 0)]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('i', 1), ('j', 2), ('i', 0), ('j', 1)]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('i', 2), ('j', 1), ('i', 1), ('j', 0)]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'), [('i', 0)]),
 (('ValueError', 'zip() argument 3 is longer than arguments 1-2'), [('i', 0), ('j', 1)]),
 (('KeyError', "'bad'"), [('i', 1)]),
 (('KeyError', "'bad'"), [('i', 0)]),
 (('KeyError', "'bad'"), [('a', 'end')]),
 ([(1, 0), (0, 1)], [('i', 2), ('seq', 0), ('i', 1), ('seq', 1), ('i', 0), ('seq', 2)]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('seq', 0), ('i', 2), ('seq', 1), ('i', 1)]),
 ([(1, 0, 5)], [('a', 1), ('i', 1), ('c', 5), ('a', 'end')]),
 ([(2, 5)], [('i', 3), ('c', 5), ('i', 2), ('c', 'end')]),
 ([1, 0], [('i', 2), ('a', 2), ('i', 1), ('a', 3), ('i', 0), ('a', 'end')]),
 (('ValueError', 'map() argument 2 is longer than argument 1'),
  [('i', 1), ('a', 2), ('i', 0), ('a', 3)]),
 (('ValueError', 'map() argument 3 is longer than arguments 1-2'),
  [('a', 2), ('i', 1), ('j', 2), ('a', 'end'), ('i', 0), ('j', 1)]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('i', 2), ('j', 1), ('i', 1), ('j', 0)]),
 (((1, 0, 5),), [('a', 1), ('i', 1), ('c', 5), ('a', 'end'), ('i', 0), ('c', 'end')]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('a', 1), ('i', 2), ('a', 'end'), ('i', 1)]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('a', 1), ('i', 1), ('a', 2), ('i', 0)]),
 (((1, 1), (0, 2)), [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0), ('a', 'end')]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('i', 1), ('a', 1), ('i', 0), ('a', 2)]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('i', 2), ('a', 1), ('i', 1), ('a', 'end')]),
 (((0, 0),), [('i', 1), ('j', 1), ('i', 0), ('j', 0)]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('i', 1), ('j', 2), ('i', 0), ('j', 1)]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('i', 2), ('j', 1), ('i', 1), ('j', 0)]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'), [('i', 0)]),
 (('ValueError', 'zip() argument 3 is longer than arguments 1-2'), [('i', 0), ('j', 1)]),
 (('KeyError', "'bad'"), [('i', 1)]),
 (('KeyError', "'bad'"), [('i', 0)]),
 (('KeyError', "'bad'"), [('a', 'end')]),
 (((1, 0), (0, 1)), [('i', 2), ('seq', 0), ('i', 1), ('seq', 1), ('i', 0), ('seq', 2)]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('seq', 0), ('i', 2), ('seq', 1), ('i', 1)]),
 (((1, 0, 5),), [('a', 1), ('i', 1), ('c', 5), ('a', 'end')]),
 (((2, 5),), [('i', 3), ('c', 5), ('i', 2), ('c', 'end')]),
 ((1, 0), [('i', 2), ('a', 2), ('i', 1), ('a', 3), ('i', 0), ('a', 'end')]),
 (('ValueError', 'map() argument 2 is longer than argument 1'),
  [('i', 1), ('a', 2), ('i', 0), ('a', 3)]),
 (('ValueError', 'map() argument 3 is longer than arguments 1-2'),
  [('a', 2), ('i', 1), ('j', 2), ('a', 'end'), ('i', 0), ('j', 1)]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('i', 2), ('j', 1), ('i', 1), ('j', 0)]),
 ([(1, 0, 5)], [('a', 1), ('i', 1), ('c', 5), ('a', 'end'), ('i', 0), ('c', 'end')]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('a', 1), ('i', 2), ('a', 'end'), ('i', 1)]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('a', 1), ('i', 1), ('a', 2), ('i', 0)]),
 ([(1, 1), (0, 2)], [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0), ('a', 'end')]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('i', 1), ('a', 1), ('i', 0), ('a', 2)]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('i', 2), ('a', 1), ('i', 1), ('a', 'end')]),
 ([(0, 0)], [('i', 1), ('j', 1), ('i', 0), ('j', 0)]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('i', 1), ('j', 2), ('i', 0), ('j', 1)]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('i', 2), ('j', 1), ('i', 1), ('j', 0)]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'), [('i', 0)]),
 (('ValueError', 'zip() argument 3 is longer than arguments 1-2'), [('i', 0), ('j', 1)]),
 (('KeyError', "'bad'"), [('i', 1)]),
 (('KeyError', "'bad'"), [('i', 0)]),
 (('KeyError', "'bad'"), [('a', 'end')]),
 ([(1, 0), (0, 1)], [('i', 2), ('seq', 0), ('i', 1), ('seq', 1), ('i', 0), ('seq', 2)]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('seq', 0), ('i', 2), ('seq', 1), ('i', 1)]),
 ([(1, 0, 5)], [('a', 1), ('i', 1), ('c', 5), ('a', 'end')]),
 ([(2, 5)], [('i', 3), ('c', 5), ('i', 2), ('c', 'end')]),
 ([1, 0], [('i', 2), ('a', 2), ('i', 1), ('a', 3), ('i', 0), ('a', 'end')]),
 (('ValueError', 'map() argument 2 is longer than argument 1'),
  [('i', 1), ('a', 2), ('i', 0), ('a', 3)]),
 (('ValueError', 'map() argument 3 is longer than arguments 1-2'),
  [('a', 2), ('i', 1), ('j', 2), ('a', 'end'), ('i', 0), ('j', 1)]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('i', 2), ('j', 1), ('i', 1), ('j', 0)]),
 ({1: 0}, [('a', 1), ('i', 1), ('c', 5), ('a', 'end'), ('i', 0), ('c', 'end')]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('a', 1), ('i', 2), ('a', 'end'), ('i', 1)]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('a', 1), ('i', 1), ('a', 2), ('i', 0)]),
 ({0: 2, 1: 1}, [('i', 2), ('a', 1), ('i', 1), ('a', 2), ('i', 0), ('a', 'end')]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('i', 1), ('a', 1), ('i', 0), ('a', 2)]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('i', 2), ('a', 1), ('i', 1), ('a', 'end')]),
 ({0: 0}, [('i', 1), ('j', 1), ('i', 0), ('j', 0)]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('i', 1), ('j', 2), ('i', 0), ('j', 1)]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('i', 2), ('j', 1), ('i', 1), ('j', 0)]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'), [('i', 0)]),
 (('ValueError', 'zip() argument 3 is longer than arguments 1-2'), [('i', 0), ('j', 1)]),
 (('KeyError', "'bad'"), [('i', 1)]),
 (('KeyError', "'bad'"), [('i', 0)]),
 (('KeyError', "'bad'"), [('a', 'end')]),
 ({0: 1, 1: 0}, [('i', 2), ('seq', 0), ('i', 1), ('seq', 1), ('i', 0), ('seq', 2)]),
 (('ValueError', 'zip() argument 2 is longer than argument 1'),
  [('seq', 0), ('i', 2), ('seq', 1), ('i', 1)]),
 ({1: 0}, [('a', 1), ('i', 1), ('c', 5), ('a', 'end')]),
 ({2: 5}, [('i', 3), ('c', 5), ('i', 2), ('c', 'end')]),
 (('TypeError', 'cannot unpack non-iterable int object'), [('i', 2), ('a', 2)]),
 (('TypeError', 'cannot unpack non-iterable int object'), [('i', 1), ('a', 2)]),
 (('TypeError', 'cannot unpack non-iterable int object'), [('a', 2), ('i', 1), ('j', 2)]),
 (('ValueError', 'zip() argument 2 is shorter than argument 1'),
  [('i', 2), ('j', 1), ('i', 1), ('j', 0)]),
 ([((1, 1), [('a', 1), ('i', 2)]),
   (('ValueError', 'zip() argument 2 is longer than argument 1'), [('a', 'end'), ('i', 1)]),
   (('StopIteration', ''), [('i', 0)])],
  ('d', [('i', 0)])),
 [((0, 3), [('i', 1), ('b', 3)]),
  (('ValueError', 'zip() argument 2 is longer than argument 1'), [('i', 0), ('b', 4)]),
  (('StopIteration', ''), [('i', 0), ('b', 'end')])],
 [((0, 1), [('i', 1), ('j', 2)]),
  (('ValueError', 'zip() argument 2 is longer than argument 1'), [('i', 0), ('j', 1)]),
  (('StopIteration', ''), [('i', 0), ('j', 0)])]]
assert_eq(out, expected)
