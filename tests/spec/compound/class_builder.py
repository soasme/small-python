# spec: PLS-315 16.4.1, 19.3.38, 9.3.2
# description: A class statement calls __build_class__ from its frame's builtins, which may be any mapping.
from harness import *

builtin_builder = __build_class__
log = []
def builder(func, name, *bases, **kwds):
    log.append((type(func).__name__, func.__name__, func.__qualname__, name, bases, kwds))
    return builtin_builder(func, name, *bases, **kwds)
class Base: pass
source = """
class A: x = 1
class B(A, metaclass=type):
    def m(self): return __class__
def f():
    class Inner: z = 2
    return Inner
I = f()
"""
ns = {"__builtins__": {"__build_class__": builder, "type": type}, "__name__": "mod"}
exec(source, ns)
assert_eq(log, [("function", "A", "A", "A", (), {}),
                ("function", "B", "B", "B", (ns["A"],), {"metaclass": type}),
                ("function", "Inner", "f.<locals>.Inner", "Inner", (), {})])
assert_eq((ns["A"].x, ns["B"]().m() is ns["B"], ns["I"].z, ns["I"].__qualname__, ns["A"].__module__),
          (1, True, 2, "f.<locals>.Inner", "mod"))

# The builder's result is the class, whatever it is.
ns = {"__builtins__": {"__build_class__": lambda func, name, *b, **k: (name, b, k), "int": int}}
exec("class C(int, flag=1): pass", ns)
assert_eq(ns["C"], ("C", (int,), {"flag": 1}))
# A generic class passes its Generic base.
log.clear()
ns = {"__builtins__": dict(vars(builtin_builder.__self__), __build_class__=builder)}
exec("class G[T]: pass", ns)
assert_eq((log[0][3], len(log[0][4]), ns["G"].__type_params__[0].__name__), ("G", 1, "T"))

e = assert_raises(NameError, exec, "class D: pass", {"__builtins__": {}})
assert_eq(str(e), "__build_class__ not found")

# Builtins that are not exactly a dict are read by subscription.
class Mapping:
    def __init__(self): self.keys = []
    def __getitem__(self, key):
        self.keys.append(key)
        if key == "len": return lambda x: 42
        if key == "__build_class__": return builtin_builder
        raise KeyError(key)
m = Mapping()
assert_eq(eval("len('a')", {"__builtins__": m}), 42)
assert_eq(str(assert_raises(NameError, eval, "nope", {"__builtins__": m})), "name 'nope' is not defined")
assert_eq(m.keys, ["len", "nope"])
assert_eq(eval("[len for _ in [1]][0]('a') + (lambda: len)()('z')", {"__builtins__": m}), 84)
g = {"__builtins__": m, "__name__": "mod"}
exec("class C: pass\ndef f(): return len('q')\ny = f()", g)
assert_eq((m.keys[-2], g["C"].__module__, g["y"]), ("__build_class__", "mod", 42))
e = assert_raises(TypeError, eval, "print", {"__builtins__": 5})
assert_eq(str(e), "'int' object is not subscriptable")
exec("x = 1", {"__builtins__": 5})
class Missing(dict):
    def __missing__(self, key): return "missing:" + key
assert_eq(eval("abc", {"__builtins__": Missing()}), "missing:abc")
assert_eq(eval("abc", {"__builtins__": Missing(abc=1)}), 1)
