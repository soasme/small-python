# spec: PLS-315 10.2, 20.2.5, 20.2.8
# description: Calling a class runs __new__ then __init__; object.__new__ and object.__init__ check their arguments.
from harness import *

log = []
class C:
    def __new__(cls, *args, **kwargs):
        log.append(("new", cls.__name__, args, kwargs))
        return super().__new__(cls)
    def __init__(self, *args, **kwargs):
        log.append(("init", args, kwargs))
C(1, k=2)
assert_eq(log, [("new", "C", (1,), {"k": 2}), ("init", (1,), {"k": 2})])

# type(x) with one argument returns its type; other counts need three.
assert_is(type(1), int)
e = assert_raises(TypeError, type, 1, 2)
assert_eq(str(e), "type() takes 1 or 3 arguments")
# A metaclass subclass of type with one argument is not the shortcut.
class Meta(type): pass
assert_raises(TypeError, Meta, 1)

# __init__ is skipped when __new__ returns an instance of another class.
class Other:
    def __new__(cls):
        return 42
    def __init__(self):
        log.append("never")
log.clear()
assert_eq(Other(), 42)
assert_eq(log, [])
# A subclass instance still gets __init__.
class Base:
    def __new__(cls):
        return object.__new__(Derived)
    def __init__(self):
        log.append("init")
class Derived(Base): pass
assert_type(Base(), Derived)
assert_eq(log, ["init"])

class BadInit:
    def __init__(self):
        return 1
e = assert_raises(TypeError, BadInit)
assert_eq(str(e), "__init__() should return None, not 'int'")

# A class without __new__ cannot be instantiated.
e = assert_raises(TypeError, type(iter([])))
assert_eq(str(e), "cannot create 'list_iterator' instances")

# object.__new__ checks.
e = assert_raises(TypeError, object.__new__, 1)
assert_eq(str(e), "object.__new__(X): X is not a type object (int)")
e = assert_raises(TypeError, object.__new__, int)
assert_eq(str(e), "object.__new__(int) is not safe, use int.__new__()")
class Plain: pass
e = assert_raises(TypeError, Plain, 1)
assert_eq(str(e), "Plain() takes no arguments")
class OwnNew:
    def __new__(cls, *args):
        return object.__new__(cls, *args)
e = assert_raises(TypeError, OwnNew, 1)
assert_eq(str(e), "object.__new__() takes exactly one argument (the type to instantiate)")
class OwnInit:
    def __init__(self, *args):
        object.__init__(self, *args)
e = assert_raises(TypeError, OwnInit, 1)
assert_eq(str(e), "object.__init__() takes exactly one argument (the instance to initialize)")
e = assert_raises(TypeError, object.__init__, Plain(), 1)
assert_eq(str(e), "Plain.__init__() takes exactly one argument (the instance to initialize)")
# With both overridden, extra arguments are fine.
class Both:
    def __new__(cls, *args): return object.__new__(cls)
    def __init__(self, *args): pass
Both(1, 2)
# Only __init__ overridden: object.__new__ accepts the arguments.
class InitOnly:
    def __init__(self, x): self.x = x
assert_eq(InitOnly(3).x, 3)

# Abstract classes: assigning a true __abstractmethods__ to the class.
class Abstract:
    pass
Abstract.__abstractmethods__ = frozenset({"b", "a"})
e = assert_raises(TypeError, Abstract)
assert_eq(str(e), "Can't instantiate abstract class Abstract without an implementation for abstract methods 'a', 'b'")
class OneAbstract:
    pass
OneAbstract.__abstractmethods__ = ["only"]
e = assert_raises(TypeError, OneAbstract)
assert_eq(str(e), "Can't instantiate abstract class OneAbstract without an implementation for abstract method 'only'")
# The property is not inherited, and a false value or deletion clears it.
class Concrete(OneAbstract): pass
Concrete()
OneAbstract.__abstractmethods__ = ()
OneAbstract()
Abstract.__abstractmethods__ = {"x"}
del Abstract.__abstractmethods__
Abstract()
assert_raises(AttributeError, getattr, Abstract, "__abstractmethods__")
# Binding it in the class body does not make the class abstract.
class BodyOnly:
    __abstractmethods__ = frozenset({"a"})
BodyOnly()
