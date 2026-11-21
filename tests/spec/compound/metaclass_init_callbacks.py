# spec: PLS-315 16.4.2, 16.4.3
# description: A metaclass with type's __new__ and its own __init__ makes
# the class, calls each namespace value's __set_name__ (a staticmethod's
# with the owner and name alone), then the base's __init_subclass__ with
# the keywords, and only then the metaclass's __init__; a callback's
# exception stops it, a __set_name__ one with its note; in a generator too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
def spin():
    for _ in (): pass
class Named:
    def __set_name__(self, owner, name):
        spin(); log.append(('set', owner.__name__, name))
class Fail:
    def __set_name__(self, owner, name):
        spin(); raise KeyError(name)
class Stamp:
    __set_name__ = staticmethod(lambda owner, name: log.append(('static', name)))
class Spun:
    def f(owner, name): spin(); log.append(('spun', name))
    __set_name__ = staticmethod(f)
class Init(type):
    def __init__(cls, name, bases, ns, **kw):
        spin(); log.append(('Init', name, kw, sorted(k for k in ns if not k.startswith('__'))))
class Base:
    def __init_subclass__(cls, **kw):
        spin(); log.append(('sub', cls.__name__, kw))
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e), getattr(e, '__notes__', None))
    return r if isinstance(r, tuple) else type(r).__name__ if r is not None else None, log[:]
def a():
    class A(Base, metaclass=Init, tag=1):
        x = Named(); y = Stamp(); z = Spun()
    return A
def b():
    class B(Base, metaclass=Init):
        x = Fail()
def c():
    class C(Base, metaclass=Init, bad=1):
        def __init_subclass__(cls): pass
    class D(C, bad=2): pass
class Raising:
    def __init_subclass__(cls):
        spin(); log.append('raising'); raise ValueError(cls.__name__)
def d():
    class E(Raising, metaclass=Init): x = Named()
def e():
    class F(metaclass=Init):
        x = Named()
        def m(self): return __class__
    return F, F().m() is F
emit(run(a)); emit(run(b)); emit(run(c)); emit(run(d))
emit(run(lambda: e()[1]))
def g():
    yield run(a)
emit(list(g()))
EXPECTED = [
    "('Init', [('set', 'A', 'x'), ('static', 'y'), ('spun', 'z'), ('sub', 'A', {'tag': 1}), ('Init', 'A', {'tag': 1}, ['x', 'y', 'z'])])",
    '((\'KeyError\', "\'x\'", ["Error calling __set_name__ on \'Fail\' instance \'x\' in \'B\'"]), [])',
    '((\'TypeError\', "c.<locals>.C.__init_subclass__() got an unexpected keyword argument \'bad\'", None), [(\'sub\', \'C\', {\'bad\': 1}), (\'Init\', \'C\', {\'bad\': 1}, [])])',
    "(('ValueError', 'E', None), [('set', 'E', 'x'), 'raising'])",
    "('bool', [('set', 'F', 'x'), ('Init', 'F', {}, ['m', 'x'])])",
    "[('Init', [('set', 'A', 'x'), ('static', 'y'), ('spun', 'z'), ('sub', 'A', {'tag': 1}), ('Init', 'A', {'tag': 1}, ['x', 'y', 'z'])])]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
