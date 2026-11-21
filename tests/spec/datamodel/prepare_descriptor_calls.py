# spec: PLS-315 16.4.1, 7.3.6
# description: A class statement reads its metaclass's __prepare__ like
# any attribute of a class: a descriptor's Python __get__, which may loop,
# gives it, after the bases are resolved and before the body runs, with
# the keywords; its AttributeError means none, any other error passes
# out, and a metaclass's Python __getattribute__ reads it first.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class ObscureException(Exception): pass
class FailDescr:
    def __get__(self, instance, owner):
        for _ in (): pass
        log.append(("fail", instance, owner.__name__)); raise ObscureException
class Meta(type):
    __prepare__ = FailDescr()
try:
    class X(metaclass=Meta): pass
except ObscureException: emit("obscure", log)
def prepare(name, bases, **kw):
    log.append(("prepare", name, bases, kw)); return {"pre": 1}
class Gives:
    def __get__(self, instance, owner):
        for _ in (): pass
        log.append(("gives", owner.__name__))
        return prepare
class M2(type):
    __prepare__ = Gives()
    def __new__(m, name, bases, ns, **kw): return super().__new__(m, name, bases, ns)
log.clear()
class Base: pass
class Y(Base, metaclass=M2, k=1):
    z = 2
emit(Y.pre, Y.z, log)
class Missing:
    def __get__(self, instance, owner):
        for _ in (): pass
        log.append("missing"); raise AttributeError("no")
class M3(type):
    __prepare__ = Missing()
log.clear()
class W(metaclass=M3): q = 1
emit(W.q, type(W.__dict__).__name__, log)
class Entries:
    def __mro_entries__(self, bases):
        for _ in (): pass
        log.append("entries"); return (Base,)
log.clear()
class V(Entries(), metaclass=M2): pass
emit(V.__bases__, V.__orig_bases__[0].__class__.__name__, log)
class Hooked(type):
    def __getattribute__(cls, name):
        log.append(("ga", name)); return super().__getattribute__(name)
class MM(type, metaclass=Hooked): pass
log.clear()
class U(metaclass=MM): pass
emit(type(U).__name__, log)
EXPECTED = [
    "obscure [('fail', None, 'Meta')]",
    "1 2 [('gives', 'M2'), ('prepare', 'Y', (<class '__main__.Base'>,), {'k': 1})]",
    "1 mappingproxy ['missing']",
    "(<class '__main__.Base'>,) Entries ['entries', ('gives', 'M2'), ('prepare', 'V', (<class '__main__.Base'>,), {})]",
    "MM [('ga', '__prepare__'), ('ga', '__name__')]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
