# spec: PLS-315 7.3.5, 7.3.6, 10.3
# description: a descriptor's __get__ that is a callable instance is called
# as it is, unbound, with the descriptor, the instance or None, and the
# owner, through instances, classes and super(), its own __get__ ignored;
# an AttributeError it raises falls back to __getattr__; the instance
# dictionary precedes a non-data descriptor; a classmethod is not callable.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class CallableGet:
    def __call__(self, *args):
        for _ in (): pass
        log.append(len(args)); return tuple(type(a).__name__ for a in args[1:])
class Raising:
    def __call__(self, *args):
        for _ in (): pass
        raise AttributeError('nope')
class D: pass
class DS:
    def __set__(self, i, v): pass
class Owner:
    d = D()
    ds = DS()
    def __getattr__(self, name): return 'fallback ' + name
class Base: pass
class Sub(Base):
    def m(self): return super().d
Base.d = D()
o = Owner()
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
D.__get__ = CallableGet()
DS.__get__ = CallableGet()
for f in (lambda: o.d, lambda: Owner.d, lambda: o.ds, lambda: getattr(o, 'd'), lambda: Sub().m(), lambda: [o.d for _ in (0,)]):
    emit(repr(run(f)))
D.__get__ = Raising()
for f in (lambda: o.d, lambda: Owner.d):
    emit(repr(run(f)))
o.__dict__['d'] = 'own'
D.__get__ = CallableGet()
emit(repr(run(lambda: o.d)), repr(run(lambda: o.ds)))
def g(): yield run(lambda: o.ds)
emit(list(g()))
class Bound:
    def __get__(self, i, o): raise AssertionError('bound')
    def __call__(self, *args):
        for _ in (): pass
        log.append('b'); return len(args)
D.__get__ = Bound()
emit(repr(run(lambda: Owner.d)), repr(run(lambda: Sub().m())))
D.__get__ = classmethod(lambda *a: a)
emit(repr(run(lambda: Owner.d)))
EXPECTED = [
    "(('Owner', 'type'), [3])",
    "(('NoneType', 'type'), [3])",
    "(('Owner', 'type'), [3])",
    "(('Owner', 'type'), [3])",
    "(('Sub', 'type'), [3])",
    "([('Owner', 'type')], [3])",
    "('fallback d', [])",
    "(('AttributeError', 'nope'), [])",
    "('own', []) (('Owner', 'type'), [3])",
    "[(('Owner', 'type'), [3])]",
    "(3, ['b']) (3, ['b'])",
    '((\'TypeError\', "\'classmethod\' object is not callable"), [])',
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
