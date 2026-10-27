# spec: PLS-315 6.1
# description: Identity, type, value; None, NotImplemented, Ellipsis; default equality and hashing; __hash__ rules.
from harness import *

# Every object has an identity, a type, and a value; identity never changes.
class Thing: pass
a, b = Thing(), Thing()
assert_true(a is a and a is not b and id(a) != id(b))
assert_is(type(a), Thing)
assert_is(a.__class__, Thing)
assert_is(type(Thing), type)
assert_is(type(type), type)
assert_true(isinstance(type, object) and isinstance(object, type))

# The singletons.
assert_is(type(None)(), None)
assert_eq((repr(None), repr(NotImplemented), repr(Ellipsis), repr(...)), ("None", "NotImplemented", "Ellipsis", "Ellipsis"))
assert_false(None)
assert_true(Ellipsis)
assert_raises(TypeError, bool, NotImplemented)
assert_raises(TypeError, type(None), 1)

# Default equality is identity; default hash is consistent with it.
assert_true(a == a and a != b and not (a == b))
assert_eq(hash(a), hash(a))
assert_eq(object.__eq__(a, b), NotImplemented)
assert_eq(object.__ne__(a, a), False)
# Defining __eq__ without __hash__ makes instances unhashable.
class Eq:
    def __eq__(self, other): return True
assert_is(Eq.__hash__, None)
assert_raises(TypeError, hash, Eq())
e = assert_raises(TypeError, lambda: {Eq()})
# Inheriting __hash__ explicitly keeps it.
class EqHash(Eq):
    __hash__ = object.__hash__
assert_eq(type(hash(EqHash())), int)
# A subclass that defines __eq__ again also loses the inherited __hash__.
class Hashable:
    def __hash__(self): return 7
class Child(Hashable):
    def __eq__(self, other): return False
assert_is(Child.__hash__, None)
class Keeps(Hashable): pass
assert_eq(hash(Keeps()), 7)
# __hash__ = None blocks hashing and makes isinstance checks see it as unhashable.
class Blocked:
    __hash__ = None
assert_raises(TypeError, hash, Blocked())
# __hash__ results are truncated to the hash width; it must return an int.
class Big:
    def __hash__(self): return 2 ** 100
assert_eq(type(hash(Big())), int)
class NotInt:
    def __hash__(self): return "x"
e = assert_raises(TypeError, hash, NotInt())
assert_eq(str(e), "__hash__ method should return an integer")
class BoolHash:
    def __hash__(self): return True
assert_eq(hash(BoolHash()), 1)

# __ne__ defaults to the inverse of __eq__ unless that returns NotImplemented.
class OnlyEq:
    def __init__(self, v): self.v = v
    def __eq__(self, other): return isinstance(other, OnlyEq) and self.v == other.v
assert_true(OnlyEq(1) != OnlyEq(2))
assert_false(OnlyEq(1) != OnlyEq(1))
# Reflected comparisons: when both return NotImplemented, == falls back to identity.
class Never:
    def __eq__(self, other): return NotImplemented
n = Never()
assert_true(n == n and n != Never())
# Ordering without definitions raises TypeError.
e = assert_raises(TypeError, lambda: Thing() < Thing())
assert_eq(str(e), "'<' not supported between instances of 'Thing' and 'Thing'")
# A subclass's reflected method is tried first.
class Base:
    def __lt__(self, other): return "base"
class Derived(Base):
    def __gt__(self, other): return "derived"
assert_eq(Base() < Derived(), "derived")

# Immutability is about the container: a tuple can hold mutable objects.
t = ([],)
t[0].append(1)
assert_eq(t, ([1],))
assert_raises(TypeError, hash, t)
# Builtin types are immutable; their attributes cannot be set.
assert_raises(TypeError, setattr, int, "x", 1)
assert_raises(TypeError, setattr, object, "x", 1)
assert_raises(AttributeError, setattr, 1, "x", 1)
# Instances of user classes can get new attributes; __class__ can change between compatible classes.
class Other: pass
a.__class__ = Other
assert_is(type(a), Other)
assert_raises(TypeError, setattr, a, "__class__", int)
assert_raises(TypeError, setattr, 1, "__class__", bool)

# object.__repr__ names the module (omitting builtins) and qualified name.
class Outer:
    class Inner: pass
assert_true(repr(Outer.Inner()).startswith("<__main__.Outer.Inner object at "))
assert_true(repr(object()).startswith("<object object at "))

# Emulating buffer types (PEP 688): __buffer__ returns a memoryview.
class Exporter:
    def __buffer__(self, flags): return memoryview(b"hi")
assert_eq((bytes(Exporter()), bytearray(Exporter()), memoryview(Exporter()).tobytes()), (b"hi", bytearray(b"hi"), b"hi"))
assert_eq((b"x" + Exporter(), b"-".join([Exporter(), b"!"]), b"ahi".find(Exporter()), b"hi!".startswith(Exporter())), (b"xhi", b"hi-!", 1, True))
class BadExporter:
    def __buffer__(self, flags): return b"not a view"
assert_raises(TypeError, memoryview, BadExporter())
# Subclasses of str and bytes are accepted wherever their base is.
class Text(str): pass
class Data(bytes): pass
assert_eq(("abc".find(Text("c")), b"abc".find(Data(b"b")), "ab".endswith((Text("b"),))), (2, 1, True))

# Modules: __annotate__ is None without annotations; __dict__ is read-only;
# deleting a missing attribute names the type.
module = type(__import__("builtins"))("m")
assert_eq((module.__annotate__, module.__annotations__), (None, {}))
assert_raises(AttributeError, setattr, module, "__dict__", {})
error = assert_raises(AttributeError, delattr, module, "nope")
assert_eq(str(error), "'module' object has no attribute 'nope'")
