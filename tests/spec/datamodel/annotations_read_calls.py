# spec: PLS-315 16.6.2, 19.3.11
# description: getattr() and hasattr() of a function's, class's or
# module's __annotations__, and a staticmethod's or classmethod's, call
# its Python __annotate__(1) once, as the attribute does, the dict kept by
# the object and in the wrapper's __dict__; a non-dict result raises
# TypeError each time, a NameError propagates, and an AttributeError gives
# getattr()'s default or hasattr()'s False. Inside functions as at module
# level.
from harness import *

log = []
def note(value):
    log.append(value)
    return value

def taken(f):
    try:
        r = f()
    except Exception as e:
        r = type(e).__name__
    got = list(log); log.clear()
    return r, got

def plain(x: note(int)): pass
assert_eq(taken(lambda: (getattr(plain, "__annotations__"), getattr(plain, "__annotations__"))), (({"x": int}, {"x": int}), [int]))
def held(x: note(str)): pass
assert_eq(taken(lambda: (hasattr(held, "__annotations__"), held.__annotations__)), ((True, {"x": str}), [str]))
def missing(x: note(int).nope): pass
assert_eq(taken(lambda: (getattr(missing, "__annotations__", "default"), hasattr(missing, "__annotations__"))), (("default", False), [int, int]))
def unbound(x: undefined_name): pass
assert_eq(taken(lambda: getattr(unbound, "__annotations__")), ("NameError", []))
def listed(): pass
listed.__annotate__ = lambda format: [note(format)]
assert_eq(taken(lambda: getattr(listed, "__annotations__")), ("TypeError", [1]))
assert_eq(taken(lambda: getattr(listed, "__annotations__", None)), ("TypeError", [1]))

class Annotated:
    y: note(float)
assert_eq(taken(lambda: (getattr(Annotated, "__annotations__"), Annotated.__annotations__)), (({"y": float}, {"y": float}), [float]))

def wrapped(z: note(bytes)): pass
static = staticmethod(wrapped)
assert_eq(taken(lambda: (static.__annotations__, static.__annotations__)), (({"z": bytes}, {"z": bytes}), [bytes]))
assert_true(static.__dict__["__annotations__"] is wrapped.__annotations__)
def method(z: note(complex)): pass
bound = classmethod(method)
assert_eq(taken(lambda: (getattr(bound, "__annotations__"), bound.__dict__["__annotations__"])), (({"z": complex}, {"z": complex}), [complex]))
class Inner:
    w: note(list)
assert_eq(taken(lambda: staticmethod(Inner).__annotations__), ({"w": list}, [list]))

def inside():
    def local(a: note(dict)): pass
    def other(b: note(set)): pass
    return getattr(local, "__annotations__"), staticmethod(other).__annotations__, hasattr(other, "__annotations__")
assert_eq(taken(inside), (({"a": dict}, {"b": set}, True), [dict, set]))
