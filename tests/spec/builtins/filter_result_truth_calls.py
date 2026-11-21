# spec: PLS-315 27.1.5, 7.5.1
# description: A filter tests what its Python function returns by that
# object's Python __bool__ or __len__, which may loop, raise or return a
# non-bool, in a list, a comprehension, sum(), a yield from, under map()
# and next(); and a filter of None or bool over a generator tests each
# item it yields the same way.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Truth:
    def __init__(s, v): s.v = v
    def __bool__(s):
        for _ in (): pass
        log.append(("b", s.v)); return s.v
class Sized:
    def __init__(s, n): s.n = n
    def __len__(s):
        for _ in (): pass
        log.append(("l", s.n)); return s.n
class Bad:
    def __bool__(s):
        for _ in (): pass
        return 1
class Raise:
    def __bool__(s):
        for _ in (): pass
        raise KeyError("t")
def obj(x):
    for _ in (): pass
    return Truth(x > 1)
def sized(x):
    for _ in (): pass
    return Sized(x % 2)
emit(list(filter(obj, range(4))), log); log.clear()
emit([x for x in filter(sized, range(4))], log); log.clear()
emit(sum(filter(obj, range(5))), log); log.clear()
def g(): yield from filter(obj, [0, 2, 3])
emit(list(g()), log); log.clear()
try: list(filter(lambda x: Bad(), [1]))
except TypeError as e: emit("te", e)
f = filter(lambda x: Raise() if x == 1 else True, range(3))
try:
    for x in f: emit("item", x)
except KeyError as e: emit("ke", e)
emit(list(f))
emit(list(map(abs, filter(obj, [-5, 3, 1]))), log); log.clear()
emit(next(filter(obj, iter([1, 7]))), log)
def gen(*items):
    for item in items: yield item
emit([type(x).__name__ for x in filter(None, gen(Truth(True), Truth(False), 0, 5, Sized(2)))], log); log.clear()
emit([type(x).__name__ for x in filter(bool, gen(Sized(0), Truth(True)))], log); log.clear()
emit(list(map(type, filter(None, gen(Truth(True), -2)))) == [Truth, int], log); log.clear()
try: list(filter(None, gen(Bad())))
except TypeError as e: emit("te2", e)
EXPECTED = [
    "[2, 3] [('b', False), ('b', False), ('b', True), ('b', True)]",
    "[1, 3] [('l', 0), ('l', 1), ('l', 0), ('l', 1)]",
    "9 [('b', False), ('b', False), ('b', True), ('b', True), ('b', True)]",
    "[2, 3] [('b', False), ('b', True), ('b', True)]",
    'te Bad.__bool__() must return a bool, not int',
    'item 0',
    "ke 't'",
    '[2]',
    "[3] [('b', False), ('b', True), ('b', False)]",
    "7 [('b', False), ('b', True)]",
    "['Truth', 'int', 'Sized'] [('b', False), ('b', True), ('b', True), ('b', False), ('l', 2)]",
    "['Truth'] [('l', 0), ('b', True)]",
    "True [('b', True)]",
    'te2 Bad.__bool__() must return a bool, not int',
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
