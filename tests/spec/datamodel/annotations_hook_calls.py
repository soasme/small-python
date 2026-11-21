# spec: PLS-315 16.6.2, 7.3.4
# description: type's __annotations__ getter, reached through a
# metaclass's Python __getattribute__ by super(), or called as
# type.__getattribute__, reads __annotate__ by attribute lookup that the
# hook sees, calls it once and keeps the dict; a hook may answer
# __annotate__ itself, with a function, None, a non-callable or an
# AttributeError, and errors pass out.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
def note(x):
    for _ in (): pass
    log.append(x); return x
class G(type):
    def __getattribute__(cls, name):
        for _ in (): pass
        if name.startswith("__annot"): log.append(name)
        return super().__getattribute__(name)
class C(metaclass=G):
    z: note(float)
emit(C.__annotations__, log); log.clear()
emit(C.__annotations__, log); log.clear()
emit(type.__getattribute__(C, "__annotations__"), log); log.clear()
class H(type):
    def __getattr__(cls, name):
        for _ in (): pass
        log.append(("ga", name)); raise AttributeError(name)
class D(metaclass=H):
    w: note(int)
emit(type.__getattribute__(D, "__annotations__"), log); log.clear()
class Bad(metaclass=G):
    x: 1/0
try: Bad.__annotations__
except ZeroDivisionError: emit("zde", log); log.clear()
class Wrong(metaclass=G): pass
Wrong.__annotate__ = lambda format: 5
try: Wrong.__annotations__
except TypeError as e: emit(e, log); log.clear()
class Other(type):
    def __getattribute__(cls, name):
        if name == "__annotate__": return lambda format: {"made": format}
        return super().__getattribute__(name)
class E(metaclass=Other):
    q: int
emit(E.__annotations__, E.__dict__.get("__annotations_cache__"))
class F(metaclass=Other): pass
emit(F.__annotations__)
class NotCallable(type):
    def __getattribute__(cls, name):
        if name == "__annotate__": return 5
        return super().__getattribute__(name)
class K(metaclass=NotCallable):
    q: int
emit(K.__annotations__)
class NoneAnnotate(type):
    def __getattribute__(cls, name):
        if name == "__annotate__": return None
        return super().__getattribute__(name)
class L(metaclass=NoneAnnotate):
    q: int
emit(L.__annotations__)
class Raising(type):
    def __getattribute__(cls, name):
        if name == "__annotate__": raise AttributeError("gone")
        return super().__getattribute__(name)
class R(metaclass=Raising):
    q: int
try: emit(R.__annotations__)
except AttributeError as e: emit("ae", e)
emit(type.__getattribute__(C, "__annotations__") is C.__annotations__)
EXPECTED = [
    "{'z': <class 'float'>} ['__annotations__', '__annotate__', <class 'float'>]",
    "{'z': <class 'float'>} ['__annotations__']",
    "{'z': <class 'float'>} []",
    "{'w': <class 'int'>} [<class 'int'>]",
    "zde ['__annotations__', '__annotate__']",
    "__annotate__() must return a dict, not int ['__annotations__', '__annotate__']",
    "{'made': 1} {'made': 1}",
    "{'made': 1}",
    '{}',
    '{}',
    'ae gone',
    'True',
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
