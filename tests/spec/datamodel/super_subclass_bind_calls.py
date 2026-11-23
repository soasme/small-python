# spec: PLS-315 20.3.2, 7.3.5
# description: An unbound super object of a subclass of super, read
# through an instance, is bound by calling that subclass, whose Python
# __init__ may loop or raise, with its __thisclass__ and the instance: by
# an attribute, getattr() with or without a default, hasattr() and
# object.__getattribute__; an instance's own entry comes first, the
# class's read gives it unbound, and the AttributeError it raises gives
# way to __getattr__.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class A:
    def meth(self, a): return "A(%r)" % a
class mysuper(super):
    def __init__(self, *args):
        for _ in (): pass
        log.append(len(args))
        return super(mysuper, self).__init__(*args)
class F(A):
    def meth(self, a):
        s = self.__super
        return "F(%r)[%s]" % (a, s.__class__.__name__) + s.meth(a)
F._F__super = mysuper(F)
emit(F().meth(6), log); log.clear()
emit(F.__dict__["_F__super"].__class__.__name__, F._F__super.__class__.__name__, log); log.clear()
armed = []
class Odd(super):
    def __init__(self, *args):
        for _ in (): pass
        if armed: raise ValueError(len(args))
        super().__init__(*args)
class G(A):
    pass
G.attr = Odd(G)
armed.append(1)
try: G().attr
except ValueError as e: emit("ve", e)
class H(A):
    def __getattr__(self, name):
        for _ in (): pass
        return "fallback " + name
class Raising(super):
    def __init__(self, *args):
        for _ in (): pass
        if armed: raise AttributeError("bound")
        super().__init__(*args)
armed.clear()
H.r = Raising(H)
armed.append(1)
emit(H().r, getattr(H(), "r"), getattr(G(), "nothere", "dflt"))
armed.clear()
emit(getattr(F(), "_F__super").__class__.__name__, log); log.clear()
emit(getattr(F(), "_F__super", 1).__class__.__name__, log); log.clear()
emit(hasattr(F(), "_F__super"), log); log.clear()
emit(object.__getattribute__(F(), "_F__super").__class__.__name__, log); log.clear()
H.s = mysuper(H)
emit(H().s.__class__.__name__, log); log.clear()
i = F(); i.__dict__["_F__super"] = 5
emit(i._F__super, log)
class Both(super):
    def __get__(self, obj, owner=None):
        for _ in (): pass
        return "own get"
G.both = Both(G)
emit(G().both)
EXPECTED = [
    'F(6)[mysuper]A(6) [1, 2]',
    'mysuper mysuper []',
    've 2',
    'fallback r fallback r dflt',
    'mysuper [2]',
    'mysuper [2]',
    'True [2]',
    'mysuper [2]',
    'mysuper [1, 2]',
    '5 []',
    'own get',
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)

# A subclass without its own __init__ binds as well.
class PlainBase:
    def who(self): return "base"
class PlainDerived(PlainBase):
    def who(self): return "derived"
class PlainSuper(super): pass
PlainDerived.up = PlainSuper(PlainDerived)
plain_derived = PlainDerived()
plain_bound = plain_derived.up
assert_eq([type(plain_bound).__name__, plain_bound.who(), plain_bound.__self__ is plain_derived], ["PlainSuper", "base", True])
