# spec: PLS-315 16.4.2
# description: A class statement whose metaclass makes no class as type's
# does calls it once with the name, resolved bases, namespace and keywords,
# after __orig_bases__ is stored: a function, which may loop, raise, or
# return what is no class, or a class whose metaclass has a Python
# __call__; a class it builds with type() fills the __class__ cell. Inside
# functions as at module level.
from harness import *

log = []
marker = object()
def func(name, bases, ns, **kw):
    for _ in (): pass
    log.append((name, bases, sorted(k for k in ns if not k.startswith("__")), kw))
    if kw.get("bad"): raise KeyError("bad")
    if kw.get("real"): return type(name, bases, ns)
    return marker
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def a():
    class X(metaclass=func):
        x = 1
    return X is marker
def b():
    class Y(object, metaclass=func, flag=2):
        def m(self): pass
    return Y is marker
def c():
    class Z(metaclass=func, bad=True): pass
def d():
    class W(metaclass=func, real=True):
        def m(self): return __class__
    return W.__name__, W().m() is W
def e():
    class V(metaclass=func):
        def m(self): return __class__
    return V is marker
class Outer(type):
    def __call__(cls, *args, **kw):
        for _ in (): pass
        log.append(("outer", cls.__name__, args[0]))
        return "made by outer"
class Meta(type, metaclass=Outer): pass
def f():
    class U(metaclass=Meta): pass
    return U
class Base:
    def __mro_entries__(self, bases): return (object,)
def g():
    class T(Base(), metaclass=func): pass
    return T is marker
expected = [(True, [("X", (), ["x"], {})]), (True, [("Y", (object,), ["m"], {"flag": 2})]),
            (("KeyError", "'bad'"), [("Z", (), [], {"bad": True})]), (("W", True), [("W", (), ["m"], {"real": True})]),
            (True, [("V", (), ["m"], {})]), ("made by outer", [("outer", "Meta", "U")]), (True, [("T", (object,), [], {})])]
assert_eq([run(t) for t in (a, b, c, d, e, f, g)], expected)
del log[:]
class M2(metaclass=func): pass
assert_is(M2, marker)
assert_eq(log, [("M2", (), [], {})])
