# spec: PLS-315 28.7, 28.8, 10.1.2
# description: Method, slot-wrapper, classmethod, getset and member descriptors of built-in types.
from harness import *

append = list.__dict__["append"]
add = list.__dict__["__add__"]
fromkeys = dict.__dict__["fromkeys"]
assert_eq(type(append).__name__, "method_descriptor")
assert_eq(type(add).__name__, "wrapper_descriptor")
assert_eq(type(fromkeys).__name__, "classmethod_descriptor")
for d, name, owner in ((append, "append", list), (add, "__add__", list), (fromkeys, "fromkeys", dict)):
    assert_eq(d.__name__, name)
    assert_eq(d.__qualname__, f"{owner.__name__}.{name}")
    assert_is(d.__objclass__, owner)
    assert_true(hasattr(d, "__doc__"))
assert_is(append.__get__(None, list), append)
bound = append.__get__([1], list)
assert_eq(type(bound).__name__, "builtin_function_or_method")
assert_eq(type([].__add__).__name__, "method-wrapper")
assert_eq(fromkeys.__get__(None, dict)("ab"), {"a": None, "b": None})
assert_eq(type(fromkeys.__get__(None, dict)).__name__, "builtin_function_or_method")
lst = []
append(lst, 1)
assert_eq(lst, [1])
assert_eq(add([1], [2]), [1, 2])
e = assert_raises(TypeError, append.__get__, (), tuple)
assert_eq(str(e), "descriptor 'append' for 'list' objects doesn't apply to a 'tuple' object")
e = assert_raises(TypeError, append, (), 1)
assert_eq(str(e), "descriptor 'append' for 'list' objects doesn't apply to a 'tuple' object")
e = assert_raises(TypeError, add, (), [])
assert_eq(str(e), "descriptor '__add__' requires a 'list' object but received a 'tuple'")
e = assert_raises(TypeError, append)
assert_eq(str(e), "unbound method list.append() needs an argument")
e = assert_raises(TypeError, add)
assert_eq(str(e), "descriptor '__add__' of 'list' object needs an argument")
assert_eq(repr(append), "<method 'append' of 'list' objects>")
assert_eq(repr(add), "<slot wrapper '__add__' of 'list' objects>")
assert_eq(repr(fromkeys), "<method 'fromkeys' of 'dict' objects>")
assert_true(repr([].__add__).startswith("<method-wrapper '__add__' of list object at "))

real = int.__dict__["real"]
assert_eq(type(real).__name__, "getset_descriptor")
assert_eq((real.__name__, real.__qualname__, real.__objclass__), ("real", "int.real", int))
assert_eq(real.__get__(5, int), 5)
assert_is(real.__get__(None, int), real)
e = assert_raises(AttributeError, real.__set__, 5, 1)
assert_eq(str(e), "attribute 'real' of 'int' objects is not writable")
assert_raises(AttributeError, real.__delete__, 5)
e = assert_raises(TypeError, real.__get__, "s", str)
assert_eq(str(e), "descriptor 'real' for 'int' objects doesn't apply to a 'str' object")
assert_eq(repr(real), "<attribute 'real' of 'int' objects>")
assert_eq(type(BaseException.__dict__["args"]).__name__, "getset_descriptor")

class Slotted:
    __slots__ = ("x",)
member = Slotted.__dict__["x"]
assert_eq(type(member).__name__, "member_descriptor")
assert_eq((member.__name__, member.__qualname__, member.__objclass__), ("x", "Slotted.x", Slotted))
assert_eq(repr(member), "<member 'x' of 'Slotted' objects>")
s = Slotted()
e = assert_raises(AttributeError, getattr, s, "x")
assert_eq(str(e), "'Slotted' object has no attribute 'x'")
member.__set__(s, 4)
assert_eq(s.x, 4)
member.__delete__(s)
assert_raises(AttributeError, getattr, s, "x")
e = assert_raises(TypeError, member.__get__, 1, int)
assert_eq(str(e), "descriptor 'x' for 'Slotted' objects doesn't apply to a 'int' object")
