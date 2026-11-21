# spec: PLS-315 16.4.2, 7.3.4
# description: A class statement reads each non-class base's
# __mro_entries__ by GetAttribute: a Python __getattribute__, property or
# __getattr__ answers it, an AttributeError means the base has none, and
# any other error propagates; in a generator too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Base: pass
class Hooked:
    def __getattribute__(self, name):
        for _ in (): pass
        log.append(('get', name))
        if name == '__mro_entries__': return lambda bases: (Base,)
        return object.__getattribute__(self, name)
class Missing:
    def __getattr__(self, name):
        for _ in (): pass
        log.append(('getattr', name)); raise AttributeError(name)
class Raising:
    def __getattribute__(self, name):
        for _ in (): pass
        raise KeyError(name)
class Prop:
    @property
    def __mro_entries__(self):
        for _ in (): pass
        log.append('prop'); return lambda bases: (Base,)
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def a():
    class A(Hooked(), Prop()): pass
    return [b.__name__ for b in A.__mro__]
def b():
    class B(Missing()): pass
def c():
    class C(Raising()): pass
def d():
    class D(list[int], Hooked()): pass
    return [x.__name__ for x in D.__bases__], D.__orig_bases__[0]
for f in (a, b, c, d): emit(run(f))
emit(run(lambda: type('E', (Base,), {}).__name__))
def g(): yield run(d)
emit(list(g()))
EXPECTED = [
    "(('TypeError', 'duplicate base class Base'), [('get', '__mro_entries__'), 'prop'])",
    "(('TypeError', 'Missing() takes no arguments'), [('getattr', '__mro_entries__')])",
    '((\'KeyError\', "\'__mro_entries__\'"), [])',
    "((['list', 'Base'], list[int]), [('get', '__mro_entries__')])",
    "('E', [])",
    "[((['list', 'Base'], list[int]), [('get', '__mro_entries__')])]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
