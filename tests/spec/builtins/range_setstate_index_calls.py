# spec: PLS-315 27.1.1, 29.9.1
# description: a range iterator's __setstate__ converts its state by the
# state's Python __index__ once, after checking the iterator it is bound
# to, and its errors pass out; a long range iterator's state must be an
# int; inside comprehensions and generators too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Two:
    def __index__(self):
        for _ in (): pass
        log.append('i'); return 2
class Bad:
    def __index__(self): return 'x'
class Boom:
    def __index__(self): raise KeyError('b')
class Big:
    def __index__(self): return 10**30
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def rs(st, src=range(5), skip=1):
    it = iter(src)
    for _ in range(skip): next(it)
    it.__setstate__(st)
    return list(it)
RI = type(iter(range(3)))
for f in (lambda: rs(Two()), lambda: rs(Bad()), lambda: rs(Boom()), lambda: rs(Big()), lambda: rs(-3), lambda: rs(Two(), range(10**20, 10**20 + 5)),
          lambda: RI.__setstate__(iter(range(5)), Two()), lambda: RI.__setstate__(iter([1]), Two()), lambda: rs(Two(), [1, 2, 3, 4]),
          lambda: iter(range(5)).__setstate__(), lambda: [rs(Two()) for _ in (0,)]):
    emit(repr(run(f)))
def g(): yield run(lambda: rs(Two()))
emit(list(g()))
EXPECTED = [
    "([3, 4], ['i'])",
    "(('TypeError', 'Bad.__index__() must return an int, not str'), [])",
    '((\'KeyError\', "\'b\'"), [])',
    "(('OverflowError', 'Python int too large to convert to C long'), [])",
    '([1, 2, 3, 4], [])',
    "(('TypeError', 'state must be an int, not Two'), [])",
    "(None, ['i'])",
    '((\'TypeError\', "descriptor \'__setstate__\' for \'range_iterator\' objects doesn\'t apply to a \'list_iterator\' object"), [])',
    "(('TypeError', 'an integer is required'), [])",
    "(('TypeError', 'range_iterator.__setstate__() takes exactly one argument (0 given)'), [])",
    "([[3, 4]], ['i'])",
    "[([3, 4], ['i'])]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
