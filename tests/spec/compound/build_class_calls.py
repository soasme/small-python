# spec: PLS-315 16.4.1, 19.3.38
# description: A class statement calls the __build_class__ its builtins
# hold, other than the builtin one, with the body as a function, the name,
# the bases and the keywords, once: a Python one, which may loop, raise, or
# return what is no class, for a body that only assigns and one that
# loops, at module level of exec'd source and inside its functions; the
# statement binds what it returns.
from harness import *

log = []
def builder(func, name, *bases, **kw):
    for _ in (): pass
    log.append((name, len(bases), sorted(kw)))
    if kw.get("bad"): raise KeyError(name)
    if kw.get("plain"): return "not a class"
    kw.pop("flag", None)
    return __build_class__(func, name, *bases, **kw)

source = """
class A:
    x = 1
class B(A, flag=1):
    for i in range(2): pass
class C(plain=True):
    y = 2
try:
    class D(bad=True): pass
except KeyError as e:
    caught = str(e)
def inner():
    class E(A):
        z = 3
    class F:
        for j in range(2): pass
    return E, F
E, F = inner()
"""
namespace = {"__name__": "src", "__builtins__": dict(vars(__build_class__.__self__), __build_class__=builder)}
exec(source, namespace)
assert_eq(log, [("A", 0, []), ("B", 1, ["flag"]), ("C", 0, ["plain"]), ("D", 0, ["bad"]), ("E", 1, []), ("F", 0, [])])
assert_eq((namespace["A"].x, namespace["B"].__bases__ == (namespace["A"],), namespace["C"], namespace["caught"]),
          (1, True, "not a class", "'D'"))
assert_eq((namespace["E"].z, namespace["E"].__bases__ == (namespace["A"],), namespace["F"].j), (3, True, 1))

# Any number of bases and keywords reach it, more than 62 bases too.
def counting(func, name, *bases, **kw):
    return (name, len(bases), kw)
many = {"__builtins__": dict(vars(__build_class__.__self__), __build_class__=counting), "bases": [object] * 70}
exec("class C(*bases, flag=1): pass", many)
assert_eq(many["C"], ("C", 70, {"flag": 1}))

# __build_class__ reads a base's __mro_entries__ through its Python
# __getattr__; a __prepare__ that fails, Python or native, stops it.
class GetattrEntry:
    def __getattr__(self, name):
        if name == "__mro_entries__": return lambda bases: (int,)
        raise AttributeError(name)
class RaisingPrepare(type):
    @classmethod
    def __prepare__(m, name, bases): raise KeyError("p")
class NativePrepare(type):
    __prepare__ = {}.__getitem__
def entry_body(): pass
entry_got = __build_class__(entry_body, "Got", GetattrEntry())
assert_eq([entry_got.__bases__, type(entry_got.__orig_bases__[0])], [(int,), GetattrEntry])
assert_raises(KeyError, lambda: __build_class__(entry_body, "Fails", GetattrEntry(), metaclass=RaisingPrepare))
assert_raises(TypeError, lambda: __build_class__(entry_body, "Fails", GetattrEntry(), metaclass=NativePrepare),
              message="dict.__getitem__() takes exactly one argument (2 given)")
