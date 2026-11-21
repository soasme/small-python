# spec: PLS-315 20.6, 20.7
# description: staticmethod() and classmethod() of an instance or class
# copy its names, a Python __getattr__ or metaclass __getattr__ answering
# the ones it lacks, an AttributeError leaving one out and another error
# passing out; in a class body and a generator too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Fn:
    def __init__(self, fail=None): self.fail = fail
    def __getattr__(self, name):
        for _ in (): pass
        log.append(name)
        if name == self.fail: raise KeyError(name)
        if name == '__qualname__': raise AttributeError(name)
        return 'v_' + name
    def __call__(self, *a): return a
class Meta(type):
    def __getattr__(cls, name):
        log.append(('meta', name)); return 'm_' + name
class K(metaclass=Meta): pass
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def attrs(w): return (type(w).__name__, w.__module__, w.__name__, getattr(w, '__qualname__', '-'), w.__doc__)
for f in (lambda: attrs(staticmethod(Fn())), lambda: attrs(classmethod(Fn())), lambda: staticmethod(Fn('__name__')),
          lambda: type(classmethod(Fn('__doc__'))).__name__, lambda: attrs(staticmethod(K)), lambda: repr(staticmethod(len)),
          lambda: staticmethod(Fn())(1), lambda: staticmethod(), lambda: attrs(staticmethod(lambda: 0))[2]):
    emit(run(f))
class C:
    m = staticmethod(Fn())
emit(C.m(5), C.__dict__['m'].__name__)
def g(): yield run(lambda: attrs(classmethod(Fn())))
emit(list(g()))
EXPECTED = [
    "(('staticmethod', '__main__', 'v___name__', '-', None), ['__name__', '__qualname__'])",
    "(('classmethod', '__main__', 'v___name__', '-', None), ['__name__', '__qualname__'])",
    '((\'KeyError\', "\'__name__\'"), [\'__name__\'])',
    "('classmethod', ['__name__', '__qualname__'])",
    "(('staticmethod', '__main__', 'K', 'K', None), [])",
    "('<staticmethod(<built-in function len>)>', [])",
    "((1,), ['__name__', '__qualname__'])",
    "(('TypeError', 'staticmethod expected 1 argument, got 0'), [])",
    "('<lambda>', [])",
    '(5,) v___name__',
    "[(('classmethod', '__main__', 'v___name__', '-', None), ['__name__', '__qualname__'])]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
