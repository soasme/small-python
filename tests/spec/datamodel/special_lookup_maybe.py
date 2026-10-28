# spec: PLS-315 7.3.2, 7.2.4, 7.6.2, 7.5.1, 7.5.6, 7.5.7, 19.3.11
# description: A special method whose descriptor raises AttributeError is absent for operations with a fallback, and an error for the rest; attribute names may be str subclasses.
from harness import *

def booh(self):
    raise AttributeError("booh")
def boom(self):
    raise KeyError("boom")

def holder(name, getter):
    return type("E", (), {name: property(getter)})

# Operations with a fallback treat the failed method as absent.
E = holder("__eq__", booh)
assert_eq((E() == E(), E() != E()), (False, True))
e = E()
assert_eq(e == e, True)
for name, op, message in [
        ("__lt__", lambda E: E() < E(), "'<' not supported between instances of 'E' and 'E'"),
        ("__add__", lambda E: E() + 1, "unsupported operand type(s) for +: 'E' and 'int'"),
        ("__radd__", lambda E: 1 + E(), "unsupported operand type(s) for +: 'int' and 'E'"),
        ("__pow__", lambda E: pow(E(), 2, 3), "unsupported operand type(s) for ** or pow(): 'E', 'int', 'int'"),
        ("__hash__", lambda E: hash(E()), "unhashable type: 'E'"),
        ("__iter__", lambda E: iter(E()), "'E' object is not iterable"),
        ("__contains__", lambda E: 1 in E(), "argument of type 'E' is not a container or iterable"),
        ("__round__", lambda E: round(E()), "type E doesn't define __round__ method")]:
    assert_eq(str(assert_raises(TypeError, op, holder(name, booh))), message, name)
# iter() takes the sequence protocol on __getitem__'s presence alone.
it = iter(holder("__getitem__", booh)())
assert_eq(str(assert_raises(AttributeError, next, it)), "booh")
assert_eq(bool(holder("__bool__", booh)()), True)
assert_eq(str(assert_raises(AttributeError, bool, holder("__len__", booh)())), "booh")
both = type("E", (), {"__bool__": property(booh), "__len__": lambda self: 0})
assert_eq(bool(both()), False)
neither = type("E", (), {"__bool__": property(booh), "__len__": property(booh)})
assert_eq(bool(neither()), True)
r = holder("__repr__", booh)()
assert_eq(repr(r)[:13], "<E object at ")
assert_eq((str(r)[:13], ascii(r)[:13], f"{r!r}"[:13], "%r" % (r,)), ("<E object at ", "<E object at ", "<E object at ", repr(r)))
# The bare type name, also for a class whose metaclass's __repr__ fails.
M = type("M", (type,), {"__repr__": property(booh)})
C = M("C", (), {})
assert_eq(repr(C)[:13], "<M object at ")
# __del__ is skipped.
D = holder("__del__", booh)
D()

# A failure in any other exception class propagates.
for name, op in [("__eq__", lambda E: E() == E()), ("__add__", lambda E: E() + 1), ("__hash__", lambda E: hash(E())),
                 ("__bool__", lambda E: bool(E())), ("__repr__", lambda E: repr(E())), ("__iter__", lambda E: iter(E())),
                 ("__contains__", lambda E: 1 in E()), ("__round__", lambda E: round(E()))]:
    assert_eq(str(assert_raises(KeyError, op, holder(name, boom))), "'boom'", name)

# Operations without a fallback raise the AttributeError.
for name, op in [("__len__", lambda E: len(E())), ("__getitem__", lambda E: E()[0]), ("__call__", lambda E: E()()),
                 ("__neg__", lambda E: -E()), ("__index__", lambda E: [][E():]), ("__str__", lambda E: str(E())),
                 ("__iadd__", None)]:
    if op is None:
        def op(E):
            x = E()
            x += 1
    assert_eq(str(assert_raises(AttributeError, op, holder(name, booh))), "booh", name)

# getattr, setattr, hasattr and delattr take a str subclass as the name.
class Name(str): pass
class Plain: pass
p = Plain()
setattr(p, Name("a"), 1)
assert_eq((p.a, getattr(p, Name("a")), hasattr(p, Name("a")), getattr(p, Name("b"), 2), list(vars(p))), (1, 1, True, 2, ["a"]))
delattr(p, Name("a"))
assert_false(hasattr(p, Name("a")))
for f, args in [(getattr, ()), (hasattr, ()), (delattr, ()), (setattr, (1,))]:
    assert_eq(str(assert_raises(TypeError, f, p, b"a", *args)), "attribute name must be string, not 'bytes'")
