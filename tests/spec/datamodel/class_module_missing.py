# spec: PLS-315 10.4.2, 16.4.3
# description: type() called under globals without __name__ makes a class
# whose namespace has no __module__: reading C.__module__ raises
# AttributeError("__module__") rather than finding a base's, its
# instances have none, a call's error names it without a module, and
# assigning __module__ gives it one. A metaclass's own __module__ is
# found as for any attribute.
from harness import *

g = {"__builtins__": {"type": type}}
exec("X = type('X', (), {})\nY = type('Y', (X,), {'__module__': 'm'})", g)
X, Y = g["X"], g["Y"]
e = assert_raises(AttributeError, lambda: X.__module__)
assert_eq((e.args, "__module__" in X.__dict__), (("__module__",), False))
e = assert_raises(AttributeError, lambda: type.__dict__["__module__"].__get__(X))
assert_eq(e.args, ("__module__",))
e = assert_raises(AttributeError, lambda: X().__module__)
assert_eq(str(e), "'X' object has no attribute '__module__'")
assert_eq((Y.__module__, repr(X)), ("m", "<class 'X'>"))
e = assert_raises(TypeError, lambda: X(**{"a": 1}, **{"a": 2}))
assert_eq(str(e), "X() got multiple values for keyword argument 'a'")

class B: pass
exec("C = type('C', (B,), {})", g2 := {"B": B, "__builtins__": {"type": type}})
assert_raises(AttributeError, lambda: g2["C"].__module__)
class M(type): pass
exec("D = M('D', (), {})", g3 := {"M": M, "__builtins__": {}})
assert_eq(g3["D"].__module__, __name__)

X.__module__ = "set"
assert_eq((X.__module__, X.__dict__["__module__"]), ("set", "set"))
g3["B"] = B
exec("E = M('E', (B,), {})", g3)
assert_eq(g3["E"].__module__, B.__module__)
class N(type):
    __module__ = property(lambda cls: "from N")
class F(metaclass=N): pass
exec("G = N('G', (), {})", g4 := {"N": N, "__builtins__": {}})
assert_eq((F.__module__, g4["G"].__module__), ("from N", "from N"))
class P(type):
    __module__ = "plain"
exec("H = P('H', (B,), {})\nI = P('I', (), {})", g5 := {"P": P, "B": B, "__builtins__": {}})
assert_eq((g5["H"].__module__, g5["I"].__module__), (B.__module__, "plain"))
