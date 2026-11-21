# spec: PLS-315 16.4.3, 7.3.4
# description: type() and type.__new__ read each non-class base's
# __mro_entries__ in order before the metaclass is calculated, through
# the base's Python __getattr__, __getattribute__ or a descriptor, which
# may loop: a found one is a TypeError, an AttributeError means none, and
# other errors pass out, all after the arguments' types are checked.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Entries:
    def __mro_entries__(self, bases): return ()
class Broken:
    def __getattr__(self, name):
        for _ in (): pass
        log.append(name); raise KeyError(name)
class Missing:
    def __getattr__(self, name):
        for _ in (): pass
        log.append(name); raise AttributeError(name)
class Found:
    def __getattr__(self, name):
        for _ in (): pass
        log.append(name); return lambda bases: ()
class Hooked:
    def __getattribute__(self, name):
        for _ in (): pass
        log.append(("ga", name)); return object.__getattribute__(self, name)
class Desc:
    def __get__(self, obj, owner):
        for _ in (): pass
        log.append("get"); raise AttributeError("no")
class Described:
    __mro_entries__ = Desc()
class Meta(type):
    def __new__(mcls, *a, **k):
        log.append("meta new"); return super().__new__(mcls, *a, **k)
class WithMeta(metaclass=Meta): pass
def attempt(*args, **kw):
    log.clear()
    try: r = type(*args, **kw); emit("made", r.__name__, log)
    except Exception as e: emit(type(e).__name__, e, log)
attempt("X", (Entries(),), {})
attempt("X", (Broken(),), {})
attempt("X", (Missing(),), {})
attempt("X", (Found(),), {})
attempt("X", (Hooked(),), {})
attempt("X", (Described(),), {})
attempt("X", (int, Missing(), Found()), {})
attempt("X", (Missing(), Missing()), {})
attempt("X", (WithMeta, Missing()), {})
attempt(1, (Missing(),), {})
attempt("X", (Missing(),), [])
attempt("X", (Missing(),), {}, k=1)
log.clear()
try: type.__new__(type, "X", (Found(),), {})
except TypeError as e: emit("new", e, log)
args = ("X", (Missing(),), {})
attempt(*args)
EXPECTED = [
    "TypeError type() doesn't support MRO entry resolution; use types.new_class() []",
    "KeyError '__mro_entries__' ['__mro_entries__']",
    "TypeError metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases ['__mro_entries__']",
    "TypeError type() doesn't support MRO entry resolution; use types.new_class() ['__mro_entries__']",
    "TypeError metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases [('ga', '__mro_entries__')]",
    "TypeError metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases ['get']",
    "TypeError type() doesn't support MRO entry resolution; use types.new_class() ['__mro_entries__', '__mro_entries__']",
    "TypeError metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases ['__mro_entries__', '__mro_entries__']",
    "TypeError metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases ['__mro_entries__']",
    'TypeError type.__new__() argument 1 must be str, not int []',
    'TypeError type.__new__() argument 3 must be dict or frozendict, not list []',
    "TypeError metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases ['__mro_entries__']",
    "new type() doesn't support MRO entry resolution; use types.new_class() ['__mro_entries__']",
    "TypeError metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases ['__mro_entries__']",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
