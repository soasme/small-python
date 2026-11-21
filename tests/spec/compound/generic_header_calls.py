# spec: PLS-315 16.7, 16.4.1
# description: A generic class's bases and keywords are evaluated in its
# type parameters' scope, after the parameters are made, their Python
# calls, which may loop, in order, in a function, a generator or a class
# body; a keyword goes to the metaclass, and an error raised there, or a
# ** value that is not a mapping, passes out of the class statement.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Base:
    def __class_getitem__(cls, item): return cls
def base():
    for _ in (): pass
    log.append("base"); return Base
def kw():
    log.append("kw"); return {}
class H[T](base(), **kw()):
    x = 1
emit(H.__bases__, H.__type_params__, log)
class G[T](Base[T]): pass
emit(G.__bases__, G.__type_params__)
def f():
    class I[U](base(), metaclass=type):
        def m(self): return U
    return I
I = f(); emit(I.__bases__, I().m(), log)
try:
    class J[T](1/0): pass
except ZeroDivisionError as e: emit("zde", e)
class Outer:
    q = Base
    class In[T](q): pass
emit(Outer.In.__bases__)
class Meta(type):
    def __new__(m, name, bases, ns, **kw):
        log.append(("meta", name, kw)); return super().__new__(m, name, bases, ns)
def flag():
    for _ in (): pass
    log.append("flag"); return 2
log.clear()
class L[*Ts](Base, metaclass=Meta, flag=flag()): pass
emit(L.__bases__, L.__type_params__, log)
def gen():
    class M[T](base()): pass
    yield M
    class N[T](base(), **kw()): pass
    yield N
log.clear(); emit([c.__name__ for c in gen()], log)
try:
    class P[T](**1): pass
except TypeError as e: emit("te", e)
EXPECTED = [
    "(<class '__main__.Base'>, <class 'typing.Generic'>) (T,) ['base', 'kw']",
    "(<class '__main__.Base'>, <class 'typing.Generic'>) (T,)",
    "(<class '__main__.Base'>, <class 'typing.Generic'>) U ['base', 'kw', 'base']",
    'zde division by zero',
    "(<class '__main__.Base'>, <class 'typing.Generic'>)",
    "(<class '__main__.Base'>, <class 'typing.Generic'>) (Ts,) ['flag', ('meta', 'L', {'flag': 2})]",
    "['M', 'N'] ['base', 'base', 'kw']",
    'te Value after ** must be a mapping, not int',
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
