# spec: reference/datamodel.html#basic-customization
# description: __new__/__init__, __repr__/__str__, __format__, __bytes__, __bool__, __hash__, rich comparisons.
from harness import *

log = []
class A:
    def __new__(cls, *args):
        log.append(("new", args))
        return super().__new__(cls)
    def __init__(self, *args):
        log.append(("init", args))
A(1, 2)
assert_eq(log, [("new", (1, 2)), ("init", (1, 2))])

# __init__ is not called when __new__ returns an object that is not an instance of cls.
log.clear()
class B:
    def __new__(cls):
        return 42
    def __init__(self):
        log.append("init")
assert_eq(B(), 42)
assert_eq(log, [])
class Sub(B): pass
# __init__ must return None.
class BadInit:
    def __init__(self):
        return 1
assert_raises(TypeError, BadInit)

# object.__new__/__init__ reject extra arguments only when not overridden.
class Plain: pass
assert_raises(TypeError, Plain, 1)
class OnlyInit:
    def __init__(self, x):
        self.x = x
assert_eq(OnlyInit(3).x, 3)
class OnlyNew:
    def __new__(cls, x):
        return super().__new__(cls)
OnlyNew(3)

# str() falls back to repr(); format() with an empty spec is str().
class R:
    def __repr__(self):
        return "R()"
assert_eq(str(R()), "R()")
assert_eq(format(R()), "R()")
assert_eq(f"{R()}", "R()")
assert_raises(TypeError, format, R(), "x")
class S:
    def __str__(self):
        return "S!"
assert_eq(str(S()), "S!")
assert_true(repr(S()).startswith("<"))
class BadStr:
    def __str__(self):
        return 1
assert_raises(TypeError, str, BadStr())
class BadRepr:
    def __repr__(self):
        return None
assert_raises(TypeError, repr, BadRepr())

class Byt:
    def __bytes__(self):
        return b"xy"
assert_eq(bytes(Byt()), b"xy")
class BadBytes:
    def __bytes__(self):
        return "no"
assert_raises(TypeError, bytes, BadBytes())

# Truth: __bool__ then __len__; __bool__ must return bool.
class L0:
    def __len__(self):
        return 0
assert_false(L0())
class L3:
    def __len__(self):
        return 3
assert_true(L3())
class BadBool:
    def __bool__(self):
        return 1
assert_raises(TypeError, bool, BadBool())
class NegLen:
    def __len__(self):
        return -1
assert_raises(ValueError, bool, NegLen())
assert_raises(ValueError, len, NegLen())
class BigLen:
    def __len__(self):
        return 2**100
assert_raises(OverflowError, len, BigLen())
class FloatLen:
    def __len__(self):
        return 1.0
assert_raises(TypeError, len, FloatLen())
class Both:
    def __bool__(self):
        return False
    def __len__(self):
        return 1
assert_false(Both())

# __eq__ without __hash__ makes instances unhashable; __hash__ result is truncated to an int.
class Eq:
    def __eq__(self, other):
        return True
assert_is(Eq.__hash__, None)
assert_raises(TypeError, hash, Eq())
class EqHash(Eq):
    def __hash__(self):
        return 2**100
assert_eq(hash(EqHash()), hash(2**100))
class BadHash:
    def __hash__(self):
        return "x"
assert_raises(TypeError, hash, BadHash())
class SubEq(Eq):
    pass
assert_is(SubEq.__hash__, None)
class KeepHash:
    def __hash__(self):
        return 5
class OverrideEq(KeepHash):
    def __eq__(self, other):
        return False
assert_is(OverrideEq.__hash__, None)  # defining __eq__ without __hash__ resets it

# Default equality is identity; != defaults to the inverse of ==.
o = object()
assert_true(o == o)
assert_false(o != o)
class OnlyEq:
    def __init__(self, v):
        self.v = v
    def __eq__(self, other):
        return self.v == other.v
assert_true(OnlyEq(1) != OnlyEq(2))
assert_false(OnlyEq(1) != OnlyEq(1))

# Reflection: the right operand's reflected method; subclass first when it overrides it.
class Base:
    def __lt__(self, other):
        return "Base.lt"
    def __gt__(self, other):
        return "Base.gt"
class Derived(Base):
    def __gt__(self, other):
        return "Derived.gt"
assert_eq(Base() < Derived(), "Derived.gt")
assert_eq(Base() < Base(), "Base.lt")
class Only:
    def __lt__(self, other):
        return NotImplemented
assert_raises(TypeError, lambda: Only() < Only())
assert_eq(3 < Base() if False else Base() > 3, "Base.gt")
assert_eq(3 < Base(), "Base.gt")
# NotImplemented for == falls back to identity.
class NI:
    def __eq__(self, other):
        return NotImplemented
n = NI()
assert_true(n == n)
assert_false(n == NI())
assert_true(n != NI())

# Conversions name the method whose result has the wrong type.
class Wrong:
    def __str__(self):
        return 1
    def __repr__(self):
        return 2
    def __bool__(self):
        return 1
    def __format__(self, spec):
        return 3
    def __bytes__(self):
        return 4
e = assert_raises(TypeError, str, Wrong())
assert_eq(str(e), "Wrong.__str__() must return a str, not int")
e = assert_raises(TypeError, repr, Wrong())
assert_eq(str(e), "Wrong.__repr__() must return a str, not int")
e = assert_raises(TypeError, bool, Wrong())
assert_eq(str(e), "Wrong.__bool__() must return a bool, not int")
e = assert_raises(TypeError, format, Wrong(), "")
assert_eq(str(e), "Wrong.__format__() must return a str, not int")
e = assert_raises(TypeError, bytes, Wrong())
assert_eq(str(e), "Wrong.__bytes__() must return a bytes, not int")
class BadInit:
    def __init__(self):
        return 1
e = assert_raises(TypeError, BadInit)
assert_eq(str(e), "__init__() should return None, not 'int'")
# Conversion hooks name the type by its qualified name, prefixed by a module
# other than __main__; a builtin subclass result stands for its value.
namespace = {"__name__": "mod"}
exec("class I(int): pass\nclass F(float): pass\nclass C(complex): pass\n"
     "class Outer:\n    class Hooks:\n        def __init__(self, value): self.value = value\n"
     "        def __int__(self): return self.value\n        def __float__(self): return self.value\n"
     "        def __complex__(self): return self.value\n        def __str__(self): return self.value\n"
     "class Index:\n    def __init__(self, value): self.value = value\n    def __index__(self): return self.value\n",
     namespace)
Hooks, Index = namespace["Outer"].Hooks, namespace["Index"]
for call, message in ((int, "mod.Outer.Hooks.__int__() must return an int, not str"),
                      (float, "mod.Outer.Hooks.__float__() must return a float, not str"),
                      (complex, "mod.Outer.Hooks.__complex__() must return a complex, not str"),
                      (str, "mod.Outer.Hooks.__str__() must return a str, not bytes")):
    e = assert_raises(TypeError, call, Hooks(b"x" if call is str else "x"))
    assert_eq(str(e), message)
e = assert_raises(TypeError, complex, 1, Index(1.5))
assert_eq(str(e), "mod.Index.__index__() must return an int, not float")
e = assert_raises(TypeError, complex, 1, object.__new__(namespace["Outer"]))
assert_eq(str(e), "complex() argument 'imag' must be a real number, not mod.Outer")
for value, call, expected in ((namespace["I"](3), int, 3), (True, int, 1), (namespace["F"](2.0), float, 2.0),
                              (namespace["C"](1j), complex, 1j)):
    result = call(Hooks(value))
    assert_eq((type(result), result), (call, expected))
for call, expected in ((int, 1), (float, 1.0), (complex, 1 + 0j)):
    result = call(Index(True))
    assert_eq((type(result), result), (call, expected))
