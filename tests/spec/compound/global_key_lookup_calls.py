# spec: PLS-315 9.3.2, 26.1
# description: a function's load of a global name whose globals dictionary
# holds a key of equal hash compares that key by its Python __eq__, whose
# error passes out; in assignments, expression statements, generators,
# comprehensions and methods.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Key:
    def __init__(self, name): self.name = name
    def __hash__(self): return hash(self.name)
    def __eq__(self, other):
        for _ in (): pass
        log.append(('eq', other)); return other == self.name
class Boom(Key):
    __hash__ = Key.__hash__
    def __eq__(self, other):
        for _ in (): pass
        raise KeyError('eq')
def plain():
    x = zz
    return x
def pair():
    x, y = zz, zz
    return x
def bare():
    zz
def gen():
    x = zz
    yield x
def comp(): return [zz for _ in (0,)]
class Holder:
    def get(self):
        v = zz
        return v
def run(f, key, value):
    del log[:]
    g = globals()
    g[key] = value
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    finally: del g[key]
    return r, log[:]
for f in (plain, pair, bare, lambda: list(gen()), comp, Holder().get):
    emit(repr(run(f, Key('zz'), 5)), repr(run(f, Boom('zz'), 6)))
EXPECTED = [
    '(5, [(\'eq\', \'zz\')]) ((\'KeyError\', "\'eq\'"), [])',
    '(5, [(\'eq\', \'zz\'), (\'eq\', \'zz\')]) ((\'KeyError\', "\'eq\'"), [])',
    '(None, [(\'eq\', \'zz\')]) ((\'KeyError\', "\'eq\'"), [])',
    '([5], [(\'eq\', \'zz\')]) ((\'KeyError\', "\'eq\'"), [])',
    '([5], [(\'eq\', \'zz\')]) ((\'KeyError\', "\'eq\'"), [])',
    '(5, [(\'eq\', \'zz\')]) ((\'KeyError\', "\'eq\'"), [])',
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
