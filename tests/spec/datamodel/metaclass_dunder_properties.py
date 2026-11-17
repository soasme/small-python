# spec: PLS-315 7.3.6
# description: a metaclass's data descriptor answers a read of its
# class's attribute first, a special name's too: a property named
# __name__, __mro__, __bases__, __base__, __class__, __dict__, __doc__,
# __module__, __annotations__ or any other replaces the value type keeps,
# its getter called with the class, read as an attribute or by getattr;
# a getter's error propagates. A plain metaclass attribute named
# __doc__ or __module__ yields to the class's own, and type's own answers
# when the metaclass defines nothing. Inside functions as at module level.
from harness import *

log = []
NAMES = ("__name__", "__mro__", "__bases__", "__base__", "__class__", "__dict__", "__doc__", "__module__", "__annotations__",
         "__type_params__", "__abstractmethods__", "__firstlineno__", "__x__")

def getter(name):
    def get(cls):
        for _ in range(2): pass
        log.append((name, cls.__qualname__))
        return "P" + name
    return property(get)

def failing(cls):
    for _ in range(2): pass
    raise LookupError("no")

def reads():
    del log[:]
    out = []
    for name in NAMES:
        M = type("M", (type,), {name: getter(name)})
        C = M("C", (), {})
        out.append(getattr(C, name))
    M = type("M", (type,), {name: getter(name) for name in NAMES})
    class C(metaclass=M): pass
    out.append((C.__name__, C.__mro__, C.__bases__, C.__base__, C.__class__, C.__dict__, C.__doc__, C.__x__))
    class F(metaclass=type("M", (type,), {"__bases__": property(failing)})): pass
    out.append(str(assert_raises(LookupError, lambda: F.__bases__)))
    class V(metaclass=type("M", (type,), {"__doc__": "meta", "__module__": "meta"})):
        "own"
    class T(metaclass=type("M", (type,), {})): pass
    out.append((V.__doc__, V.__module__, T.__name__, T.__bases__, T.__mro__ == (T, object)))
    return out, list(log)

SHOWN = ("__name__", "__mro__", "__bases__", "__base__", "__class__", "__dict__", "__doc__", "__x__")

expected = (["P" + name for name in NAMES] + [tuple("P" + name for name in SHOWN), "no", ("own", __name__, "T", (object,), True)],
            [(name, "C") for name in NAMES] + [(name, "reads.<locals>.C") for name in SHOWN])

def main():
    return reads()

assert_eq(main(), expected)
assert_eq(reads(), expected)
