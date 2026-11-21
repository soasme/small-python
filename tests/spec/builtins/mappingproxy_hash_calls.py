# spec: PLS-315 26.6, 19.3.18
# description: hash() of a mappingproxy is its mapping's hash, by the
# mapping's Python __hash__, whose errors and result checks pass out; an
# unhashable mapping makes the proxy unhashable; in comprehensions and
# generators too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class HD(dict):
    def __hash__(self):
        for _ in (): pass
        log.append('h'); return 77
class Big(dict):
    def __hash__(self):
        for _ in (): pass
        return 2**70
class Bad(dict):
    def __hash__(self):
        for _ in (): pass
        return 'x'
class Raise(dict):
    def __hash__(self):
        for _ in (): pass
        raise KeyError('k')
class M:
    def __getitem__(self, k): return k
    def keys(self): return []
    def __hash__(self):
        for _ in (): pass
        log.append('m'); return 5
P = type(type.__dict__)
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
for m in (HD(a=1), Big(), Bad(), Raise(), M(), {}, HD.__dict__):
    emit(repr(run(lambda: hash(P(m)))))
emit(repr(run(lambda: [hash(P(HD())) for _ in (0,)])))
def g(): yield run(lambda: hash(P(M())))
emit(list(g()))
EXPECTED = [
    "(77, ['h'])",
    '(512, [])',
    "(('TypeError', '__hash__ method should return an integer'), [])",
    '((\'KeyError\', "\'k\'"), [])',
    "(5, ['m'])",
    '((\'TypeError\', "unhashable type: \'dict\'"), [])',
    '((\'TypeError\', "unhashable type: \'dict\'"), [])',
    "([77], ['h'])",
    "[(5, ['m'])]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
