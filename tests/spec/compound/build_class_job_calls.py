# spec: PLS-315 19.3.38, 16.4.2
# description: An explicit __build_class__ resolves the bases by their
# __mro_entries__, prepares the namespace, runs the body (a plain function
# or a class statement's), calls the metaclass and runs type.__new__'s
# callbacks, each Python hook in order and its errors passing out; a
# statement's Python builder calling it, and a generator, do too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
import builtins
log = []
def spin():
    for _ in (): pass
class Base:
    def __init_subclass__(cls, **kw):
        spin(); log.append(('sub', cls.__name__, kw))
class Named:
    def __set_name__(self, owner, name):
        spin(); log.append(('set', name))
class Entry:
    def __mro_entries__(self, bases):
        spin(); log.append('entries'); return (Base,)
class Bad:
    def __mro_entries__(self, bases): spin(); return [Base]
class Meta(type):
    @classmethod
    def __prepare__(meta, name, bases, **kw):
        spin(); log.append(('prepare', name, kw)); return {'pre': 1}
def fmeta(name, bases, ns, **kw):
    spin(); log.append(('fmeta', name, sorted(ns), kw)); return 7
class NewMeta(type):
    def __new__(meta, name, bases, ns, **kw):
        spin(); log.append(('new', name)); return super().__new__(meta, name, bases, ns)
def body():
    spin(); log.append('body')
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    if isinstance(r, type): r = (r.__name__, [b.__name__ for b in r.__mro__], getattr(r, '__orig_bases__', None) is not None, sorted(k for k in vars(r) if not k.startswith('__')))
    return r, log[:]
emit(run(lambda: __build_class__(body, 'A', Entry(), tag=1)))
emit(run(lambda: __build_class__(body, 'B', Bad())))
emit(run(lambda: __build_class__(body, 'C', metaclass=Meta, k=2)))
emit(run(lambda: __build_class__(body, 'D', Base, metaclass=fmeta, k=3)))
emit(run(lambda: __build_class__(body, 'E', Base, metaclass=NewMeta)))
emit(run(lambda: __build_class__(lambda: 1/0, 'F')))
bb = __build_class__
def builder(func, name, *bases, **kw):
    spin(); log.append(('builder', name))
    return bb(func, name, *bases, **kw)
def stmt():
    builtins.__build_class__ = builder
    try:
        class G(Entry(), tag=4):
            x = Named()
            for i in range(2): pass
            def m(self): return __class__
        class H(Base, metaclass=fmeta): y = Named()
    finally:
        builtins.__build_class__ = bb
    return G().m() is G, H
emit(run(stmt))
def g(): yield run(lambda: __build_class__(body, 'I', Entry()))
emit(list(g()))
EXPECTED = [
    "(('A', ['A', 'Base', 'object'], True, []), ['entries', 'body', ('sub', 'A', {'tag': 1})])",
    "(('TypeError', '__mro_entries__ must return a tuple'), [])",
    "(('TypeError', 'C.__init_subclass__() takes no keyword arguments'), [('prepare', 'C', {'k': 2}), 'body'])",
    "(7, ['body', ('fmeta', 'D', [], {'k': 3})])",
    "(('E', ['E', 'Base', 'object'], False, []), ['body', ('new', 'E'), ('sub', 'E', {})])",
    "(('ZeroDivisionError', 'division by zero'), [])",
    "((True, 7), [('builder', 'G'), 'entries', ('set', 'x'), ('sub', 'G', {'tag': 4}), ('builder', 'H'), ('fmeta', 'H', ['__firstlineno__', '__module__', '__qualname__', '__static_attributes__', 'y'], {})])",
    "[(('I', ['I', 'Base', 'object'], True, []), ['entries', 'body', ('sub', 'I', {})])]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
