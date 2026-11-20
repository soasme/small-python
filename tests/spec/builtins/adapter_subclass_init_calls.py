# spec: PLS-315 19.2, 27.1.4, 27.1.6, 27.1.8
# description: Calling a subclass of zip, map, enumerate or filter whose
# __new__ is the builtin's, though it defines __init__, through a
# metaclass's __call__ too, or calling the builtin's __new__ with a
# subclass, calls each iterable's Python __iter__ in order, after an
# enumerate's start is converted, then the subclass's __init__ with the
# call's arguments; enumerate's iterable and start may be named, zip's
# and map's strict is any value's truth; an error of __iter__ or of the
# arguments propagates before __init__ runs; and so inside a generator.
from harness import assert_eq

log = []
class It:
    def __init__(self, *items): self.items = items
    def __iter__(self):
        for _ in (): pass
        log.append(('iter', self.items))
        if self.items == ('bad',): raise LookupError('bad iter')
        return iter(self.items)
class Idx:
    def __index__(self):
        for _ in (): pass
        log.append('index'); return 5
class E(enumerate):
    def __init__(self, *a, **k):
        for _ in (): pass
        log.append(('init', type(self).__name__, len(a), sorted(k)))
class Z(zip):
    def __init__(self, *a, **k): log.append('zinit')
class M(map):
    def __init__(self, f, *a): log.append('minit')
class F(filter):
    def __init__(self, f, it): log.append('finit')
class Z2(Z): pass
class Meta(type):
    def __call__(cls, *a): log.append('meta'); return super().__call__(*a)
class ZM(zip, metaclass=Meta):
    def __init__(self, *a): log.append('zminit')
class Bad(enumerate):
    def __init__(self, *a): return 5
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
cases = [
 lambda: list(E(It('a', 'b'))),
 lambda: (lambda e: (type(e).__name__, list(e)))(E(It('a'), Idx())),
 lambda: list(E(It('a'), start=2)),
 lambda: list(E(iterable=It('a'))),
 lambda: list(E(It('bad'))),
 lambda: list(E(5)),
 lambda: list(Z(It(1, 2), It(3, 4))),
 lambda: list(Z(It(1, 2), It(3), strict=True)),
 lambda: list(Z(It(1), It('bad'))),
 lambda: list(M(str, It(1, 2))),
 lambda: list(F(None, It(0, 1, 2))),
 lambda: list(Z2(It(1), It(2))),
 lambda: list(ZM(It(1), It(2))),
 lambda: list(Bad(It(1))),
 lambda: E.__new__(E, It('q')).__class__.__name__,
 lambda: isinstance(E(It()), enumerate),
 lambda: (lambda z: (type(z).__name__, list(z)))(zip.__new__(Z, It(1), It(2))),
 lambda: (lambda z: (type(z).__name__, list(z)))(zip.__new__(zip, It(1), It(2))),
 lambda: list(map.__new__(M, str, It(3))),
 lambda: list(enumerate.__new__(E, It('e'), Idx())),
 lambda: zip.__new__(int, It(1)),
 lambda: list(filter.__new__(F, None, It(0, 4))),
 lambda: list(zip.__new__(Z, It('bad'))),
 lambda: list(E(It('a'), start=Idx())),
 lambda: list(E(start=3, iterable=It('s'))),
 lambda: list(E(It('a'), begin=1)),
 lambda: list(E(It('a'), iterable=It('b'))),
 lambda: list(Z(It(1), It(2, 3), strict=False)),
 lambda: list(Z(It(1), It(2), strict=1)),
 lambda: list(Z(It(1), It(2), strict='yes')),
 lambda: list(M(str, It(1), It(2, 3), strict=True)),
 lambda: list(Z2(It(1), It(2, 5), strict=True)),
 lambda: list(ZM(It(1), strict=True)),
 lambda: list(Z(strict=True)),
 lambda: list(Bad(It('x'), start=1)),
 lambda: list(zip(It(1), It(2, 3), strict='')),
 lambda: list(zip(It(1), It(2, 3), strict=[0])),
 lambda: list(map(max, It(1), It(2, 3), strict=None)),
]
EXPECTED = [
    ([(0, 'a'), (1, 'b')], [('iter', ('a', 'b')), ('init', 'E', 1, [])]),
    (('E', [(5, 'a')]), ['index', ('iter', ('a',)), ('init', 'E', 2, [])]),
    ([(2, 'a')], [('iter', ('a',)), ('init', 'E', 1, ['start'])]),
    ([(0, 'a')], [('iter', ('a',)), ('init', 'E', 0, ['iterable'])]),
    (('LookupError', 'bad iter'), [('iter', ('bad',))]),
    (('TypeError', "'int' object is not iterable"), []),
    ([(1, 3), (2, 4)], [('iter', (1, 2)), ('iter', (3, 4)), 'zinit']),
    (('ValueError', 'zip() argument 2 is shorter than argument 1'), [('iter', (1, 2)), ('iter', (3,)), 'zinit']),
    (('LookupError', 'bad iter'), [('iter', (1,)), ('iter', ('bad',))]),
    (['1', '2'], [('iter', (1, 2)), 'minit']),
    ([1, 2], [('iter', (0, 1, 2)), 'finit']),
    ([(1, 2)], [('iter', (1,)), ('iter', (2,)), 'zinit']),
    ([(1, 2)], ['meta', ('iter', (1,)), ('iter', (2,)), 'zminit']),
    (('TypeError', "__init__() should return None, not 'int'"), [('iter', (1,))]),
    ('E', [('iter', ('q',))]),
    (True, [('iter', ()), ('init', 'E', 1, [])]),
    (('Z', [(1, 2)]), [('iter', (1,)), ('iter', (2,))]),
    (('zip', [(1, 2)]), [('iter', (1,)), ('iter', (2,))]),
    (['3'], [('iter', (3,))]),
    ([(5, 'e')], ['index', ('iter', ('e',))]),
    (('TypeError', 'zip.__new__(int): int is not a subtype of zip'), []),
    ([4], [('iter', (0, 4))]),
    (('LookupError', 'bad iter'), [('iter', ('bad',))]),
    ([(5, 'a')], ['index', ('iter', ('a',)), ('init', 'E', 1, ['start'])]),
    ([(3, 's')], [('iter', ('s',)), ('init', 'E', 0, ['iterable', 'start'])]),
    (('TypeError', "enumerate() got an unexpected keyword argument 'begin'"), []),
    (('TypeError', "argument for enumerate() given by name ('iterable') and position (1)"), []),
    ([(1, 2)], [('iter', (1,)), ('iter', (2, 3)), 'zinit']),
    ([(1, 2)], [('iter', (1,)), ('iter', (2,)), 'zinit']),
    ([(1, 2)], [('iter', (1,)), ('iter', (2,)), 'zinit']),
    (('TypeError', "M.__init__() got an unexpected keyword argument 'strict'"), [('iter', (1,)), ('iter', (2, 3))]),
    (('ValueError', 'zip() argument 2 is longer than argument 1'), [('iter', (1,)), ('iter', (2, 5)), 'zinit']),
    (('TypeError', "Meta.__call__() got an unexpected keyword argument 'strict'"), []),
    ([], ['zinit']),
    (('TypeError', "Bad.__init__() got an unexpected keyword argument 'start'"), [('iter', ('x',))]),
    ([(1, 2)], [('iter', (1,)), ('iter', (2, 3))]),
    (('ValueError', 'zip() argument 2 is longer than argument 1'), [('iter', (1,)), ('iter', (2, 3))]),
    ([2], [('iter', (1,)), ('iter', (2, 3))]),
]
assert_eq(len(cases), len(EXPECTED))
for i, (f, expected) in enumerate(zip(cases, EXPECTED)):
    assert_eq(run(f), expected, str(i))
def g():
    yield list(E(It('g'))), list(zip.__new__(Z, It('h')))
assert_eq(run(lambda: list(g())), ([([(0, 'g')], [('h',)])], [('iter', ('g',)), ('init', 'E', 1, []), ('iter', ('h',))]))
