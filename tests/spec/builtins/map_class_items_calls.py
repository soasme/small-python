# spec: PLS-315 27.1.6, 14.2
# description: A map whose function is a class with a Python __init__ or
# __new__ makes each item by that call as unpacking, next() and zip()
# take them, one at a time and stopping where the target count says;
# an exception from a call passes out; in a generator too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Box:
    def __init__(self, v):
        log.append(('init', v)); self.v = v
    def __repr__(self): return 'Box(%r)' % self.v
class New:
    def __new__(cls, v):
        log.append(('new', v)); return v * 10
class Bad:
    def __init__(self, v):
        if v == 2: raise KeyError(v)
        log.append(('bad', v))
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def unpack():
    a, b, c = map(Box, [1, 2, 3]); return a, b, c
def unpack_star():
    a, *b = map(New, (1, 2, 3)); return a, b
def unpack_short():
    a, b = map(Box, [1]); return a
def unpack_long():
    a, b = map(Box, [1, 2, 3]); return a
def unpack_bad():
    a, b, c = map(Bad, [1, 2, 3])
def nexts():
    it = map(Box, [4, 5]); return next(it), next(it), next(it, 'end')
def zipped():
    return [(x, y) for x, y in zip(map(Box, [6, 7]), 'ab')]
for f in (unpack, unpack_star, unpack_short, unpack_long, unpack_bad, nexts, zipped):
    emit(run(f))
def g(): yield run(unpack)
emit(list(g()))
EXPECTED = [
    "((Box(1), Box(2), Box(3)), [('init', 1), ('init', 2), ('init', 3)])",
    "((10, [20, 30]), [('new', 1), ('new', 2), ('new', 3)])",
    "(('ValueError', 'not enough values to unpack (expected 2, got 1)'), [('init', 1)])",
    "(('ValueError', 'too many values to unpack (expected 2)'), [('init', 1), ('init', 2), ('init', 3)])",
    "(('KeyError', '2'), [('bad', 1)])",
    "((Box(4), Box(5), 'end'), [('init', 4), ('init', 5)])",
    "([(Box(6), 'a'), (Box(7), 'b')], [('init', 6), ('init', 7)])",
    "[((Box(1), Box(2), Box(3)), [('init', 1), ('init', 2), ('init', 3)])]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
