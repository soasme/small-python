# spec: PLS-315 9.8, 9.3.4, 16.2, 16.2.1, 28.5, 19.3.12
# description: The main module's __builtins__ is the builtins module; a function's builtins come from its globals or the frame that made it; static methods of built-in types; dir() lists an object's __dict__.
from harness import *

builtins = __build_class__.__self__
FunctionType = type(lambda: None)

# The main module binds the builtins module; functions see its namespace.
assert_eq(__name__, "__main__")
assert_true(__builtins__ is builtins)
def f(): pass
assert_true(f.__builtins__ is builtins.__dict__)

# Globals without __builtins__: a function made from them takes the builtins
# of the frame that made it.
def length(s): return len(s)
fresh = {}
g = FunctionType(length.__code__, fresh)
assert_true(g.__builtins__ is builtins.__dict__)
assert_eq((g("abc"), fresh), (3, {}))
safe = {"None": None, "len": lambda s: "safe len"}
ns = {"type": type, "__builtins__": safe}
exec("def h(s): return len(s)\ninner = type(h)(h.__code__, {})\n", ns)
assert_true(ns["h"].__builtins__ is safe and ns["inner"].__builtins__ is safe)
assert_eq((ns["h"]("x"), ns["inner"]("x")), ("safe len", "safe len"))
assert_false("__builtins__" in ns["inner"].__globals__)
# A module object as __builtins__ stands for its namespace.
mod_ns = {"__builtins__": builtins}
exec("def k(): pass", mod_ns)
assert_true(mod_ns["k"].__builtins__ is builtins.__dict__)
# exec() adds the running frame's builtins to globals that lack them.
plain = {}
exec("x = 1", plain)
assert_true(plain["__builtins__"] is builtins.__dict__)

# Static methods of built-in types are unbound; allocators stay bound.
for static, owner in [(str.maketrans, str), (bytes.maketrans, bytes), (bytearray.maketrans, bytearray)]:
    assert_eq((static.__self__, static.__module__, static.__qualname__), (None, "builtins", owner.__name__ + ".maketrans"))
    assert_true(repr(static).startswith("<built-in method maketrans of type object at 0x"))
assert_eq((str.__new__.__self__, int.__new__.__self__, str.__new__.__module__), (str, int, None))
assert_eq((dict.fromkeys.__self__, dict.fromkeys.__module__, [].append.__module__, len.__module__), (dict, None, None, "builtins"))

# dir() lists the keys of an object's __dict__ with its class's attributes.
def fn(): pass
fn.extra = 1
assert_true("extra" in dir(fn) and "__code__" in dir(fn))
class C:
    def m(self): pass
C.m.marked = 2
bound = C().m
assert_true("marked" in dir(bound) and "__func__" in dir(bound))
assert_false("__code__" in dir(bound))
assert_eq(sorted(set(dir(bound)) - set(dir(type(bound)))), ["marked"])

# The function type's __dict__ has descriptors for the function attributes.
F = type(fn)
for name in ("__code__", "__defaults__", "__kwdefaults__", "__dict__", "__annotations__", "__annotate__", "__type_params__"):
    assert_eq(type(F.__dict__[name]).__name__, "getset_descriptor", name)
for name in ("__globals__", "__builtins__", "__closure__"):
    assert_eq(type(F.__dict__[name]).__name__, "member_descriptor", name)
    assert_raises(AttributeError, F.__dict__[name].__set__, fn, None)
assert_true(F.__dict__["__code__"].__get__(fn) is fn.__code__)
F.__dict__["__defaults__"].__set__(fn, (1,))
assert_eq((fn.__defaults__, F.__name__, F.__qualname__, F.__module__), ((1,), "function", "function", "builtins"))
