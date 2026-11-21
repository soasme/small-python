# spec: PLS-315 7.7.1, 7.8.3
# description: An int's or float's subclass with a Python __iter__,
# which may loop or be a generator function, is iterated by it in a
# membership test, comparing each item by a Python __eq__, and by every
# consumer; a result that is no iterator or a TypeError from __iter__ is
# the membership test's container error, other consumers' errors pass.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class I(int):
    def __iter__(self):
        for _ in (): pass
        log.append("iter"); return iter([1, 2])
i = I(5)
emit(1 in i, 3 in i, 3 not in i, log); log.clear()
emit(list(i), tuple(i), set(i), [x for x in i], sorted(i), log); log.clear()
emit(*i, sum(i), max(i), dict.fromkeys(i), log); log.clear()
class F(float):
    def __iter__(self):
        for _ in (): pass
        log.append("fiter"); yield 7
emit(7 in F(1.5), list(F(2.0)), log); log.clear()
class Bad(int):
    def __iter__(self):
        for _ in (): pass
        return 5
try: 1 in Bad()
except TypeError as e: emit("te", e)
class Raise(int):
    def __iter__(self):
        for _ in (): pass
        raise TypeError("inner")
try: 1 in Raise()
except TypeError as e: emit("te2", e)
try: list(Raise())
except TypeError as e: emit("te3", e)
class Eq:
    def __eq__(self, o):
        for _ in (): pass
        log.append(("eq", o)); return o == 2
emit(Eq() in i, log)
EXPECTED = [
    "True False True ['iter', 'iter', 'iter']",
    "[1, 2] (1, 2) {1, 2} [1, 2] [1, 2] ['iter', 'iter', 'iter', 'iter', 'iter']",
    "1 2 3 2 {1: None, 2: None} ['iter', 'iter', 'iter', 'iter']",
    "True [7] ['fiter', 'fiter']",
    "te argument of type 'Bad' is not a container or iterable",
    "te2 argument of type 'Raise' is not a container or iterable",
    'te3 inner',
    "True ['iter', ('eq', 1), ('eq', 2)]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
