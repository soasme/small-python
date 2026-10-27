# spec: reference/datamodel.html#the-standard-type-hierarchy
# description: Builtin type objects: immutable, with methods and descriptors in their __dict__, visible to dir().
from harness import *

# Builtin (static) types refuse attribute changes.
for cls in (int, object, type, ValueError, list):
    e = assert_raises(TypeError, setattr, cls, "x", 1)
    assert_eq(str(e), f"cannot set 'x' attribute of immutable type '{cls.__name__}'")
    assert_raises(TypeError, delattr, cls, "x")

# Methods live in the type's __dict__ and dir() lists them.
for cls, names in ((list, ["append", "sort", "__add__", "__iter__", "__len__"]), (dict, ["get", "keys", "__getitem__"]),
                   (int, ["bit_length", "__add__", "__radd__", "real", "numerator"]), (str, ["join", "format", "__mod__"]),
                   (object, ["__repr__", "__eq__", "__dir__", "__sizeof__", "__init_subclass__"]),
                   (type, ["__instancecheck__", "__subclasscheck__", "__or__", "__ror__", "__dir__"])):
    for name in names:
        assert_true(name in cls.__dict__, f"{cls.__name__}.__dict__ has {name}")
        assert_true(name in dir(cls), f"dir({cls.__name__}) has {name}")
assert_true("append" in dir([]))
assert_true("upper" in dir(""))
assert_false("__module__" in int.__dict__)
assert_eq(int.__module__, "builtins")
assert_is(list.__dict__["append"], list.append)
assert_eq(type(vars(int)).__name__, "mappingproxy")

# Getset and member descriptors of builtin types.
assert_eq(repr(int.real), "<attribute 'real' of 'int' objects>")
assert_eq(int.real.__get__(5), 5)
assert_eq(repr(range.start), "<member 'start' of 'range' objects>")
assert_eq(range.stop.__get__(range(2, 7)), 7)
assert_eq(slice.step.__get__(slice(1, 2, 3)), 3)
assert_is(property.fget.__get__(property(len)), len)
assert_is(classmethod.__func__.__get__(classmethod(len)), len)
assert_is(staticmethod.__wrapped__.__get__(staticmethod(len)), len)
class MyInt(int): pass
assert_eq(MyInt(4).real, 4)
assert_raises(AttributeError, setattr, MyInt(4), "real", 1)

# object.__dir__ and type.__dir__ give the default listing, for custom __dir__ methods.
class Custom:
    def __init__(self): self.field = 1
    def __dir__(self): return object.__dir__(self) + ["extra"]
names = dir(Custom())
assert_true("field" in names and "extra" in names and "__init__" in names)
class Meta(type):
    def __dir__(cls): return type.__dir__(cls) + ["meta_extra"]
class WithMeta(metaclass=Meta):
    attr = 1
assert_true("meta_extra" in dir(WithMeta) and "attr" in dir(WithMeta))

# type's methods are reachable from metaclasses through super().
class OrMeta(type):
    def __or__(cls, other): return ("or", super().__or__(other))
class O(metaclass=OrMeta): pass
assert_eq(O | int, ("or", type.__or__(O, int)))
assert_is(type.__or__(int, 1), NotImplemented)
assert_eq(type.__ror__(int, str), str | int)
assert_true(type.__instancecheck__(int, True))
assert_true(type.__subclasscheck__(int, bool))
# A class's own method beats the metaclass's.
assert_is(frozenset.__or__, frozenset.__dict__["__or__"])

# __type_params__ is the class's own, defaulting to ().
class Plain: pass
class Gen[T]: pass
class Sub(Gen[int]): pass
assert_eq(Plain.__type_params__, ())
assert_eq(int.__type_params__, ())
assert_eq(len(Gen.__type_params__), 1)
assert_eq(Sub.__type_params__, ())

# Methods added in recent versions.
assert_eq(b"a\r\nb\rc\n".splitlines(), [b"a", b"b", b"c"])
assert_eq(b"a\r\nb".splitlines(keepends=True), [b"a\r\n", b"b"])
assert_eq(bytearray(b"x\ny").splitlines(), [bytearray(b"x"), bytearray(b"y")])
assert_eq(b"abc".translate(bytes.maketrans(b"ab", b"xy")), b"xyc")
assert_raises(ValueError, bytes.maketrans, b"ab", b"c")
assert_same(float.from_number(3), 3.0)
assert_same(complex.from_number(1.5), 1.5 + 0j)
assert_raises(TypeError, float.from_number, "1")
assert_raises(TypeError, float.from_number, 1j)
class F(float): pass
assert_type(F.from_number(2), F)
assert_eq((5).__getnewargs__(), (5,))
assert_eq(True.__getnewargs__(), (1,))
assert_eq((1j).__getnewargs__(), (0.0, 1.0))
assert_eq("s".__getnewargs__(), ("s",))
assert_eq(enumerate[int].__origin__, enumerate)
assert_eq(slice[int].__args__, (int,))
assert_true(range(1).__bool__())
assert_false(range(0).__bool__())
assert_true(object().__sizeof__() > 0)

# __class__ assignment between compatible Python classes.
class A: pass
class B: pass
class S:
    __slots__ = ("x",)
a = A()
a.__class__ = B
assert_type(a, B)
e = assert_raises(TypeError, setattr, a, "__class__", S)
assert_eq(str(e), "__class__ assignment: 'S' object layout differs from 'B'")
e = assert_raises(TypeError, setattr, a, "__class__", int)
assert_eq(str(e), "__class__ assignment only supported for mutable types or ModuleType subclasses")
e = assert_raises(TypeError, setattr, a, "__class__", 1)
assert_eq(str(e), "__class__ must be set to a class, not 'int' object")
assert_raises(TypeError, delattr, a, "__class__")
assert_raises(TypeError, setattr, 1, "__class__", bool)
class I(int): pass
class J(int): pass
i = I(5)
i.__class__ = J
assert_eq((type(i), i + 1), (J, 6))

# A function's __code__ is writable: calls run the new code with the same
# defaults, given as many free variables as the function has cells.
def double(x=3):
    return x * 2
double.__code__ = (lambda x: x + 1).__code__
assert_eq((double(), double(5), double.__name__), (4, 6, "double"))
def closure():
    v = 1
    def inner():
        return v
    return inner
inner = closure()
assert_raises(ValueError, setattr, inner, "__code__", (lambda: 0).__code__)
assert_raises(TypeError, setattr, inner, "__code__", 1)
# __builtins__ is the read-only builtins namespace the function uses.
assert_true(double.__builtins__["len"] is len)
namespace = {"__builtins__": {"marker": 1}}
exec("def g(): pass", namespace)
assert_eq(namespace["g"].__builtins__, {"marker": 1})
assert_raises(AttributeError, setattr, double, "__builtins__", {})

# Built-in methods: __self__ is the object; __module__ is None for methods
# and absent from method-wrappers and descriptors; there is no __func__.
items = []
assert_true(items.append.__self__ is items)
assert_eq((items.append.__module__, len.__module__, "".join.__module__), (None, "builtins", None))
for value, absent in [(items.append, "__func__"), (items.__len__, "__func__"), (items.__len__, "__module__"),
                      (list.append, "__module__"), (object.__new__, "__objclass__")]:
    assert_false(hasattr(value, absent))
assert_true(items.__len__.__objclass__ is list)

# __base__ is the base that decides the instance layout.
class Plain: pass
class Slotted: __slots__ = ("x",)
assert_true(type("X", (Plain, int), {}).__base__ is int)
assert_true(type("Y", (Plain, Slotted), {}).__base__ is Slotted)
assert_true(type("Z", (Plain, object), {}).__base__ is Plain)

# Code objects: flags, names the body uses, the docstring constant, and
# replace(), which copies the code with some attributes changed.
def coded(a, *args, **kw):
    "coded doc"
    return len(a.real) + missing
code = coded.__code__
assert_eq(code.co_flags & 0x400000F, 0x400000F)
assert_eq(sorted(code.co_names), ["len", "missing", "real"])
assert_eq(code.co_consts[0], "coded doc")
renamed = code.replace(co_name="other", co_firstlineno=7)
assert_eq((renamed.co_name, renamed.co_firstlineno, code.co_name), ("other", 7, "coded"))
assert_true(code.replace() == code and hash(code.replace()) == hash(code) and renamed != code)
coded.__code__ = renamed
assert_true(coded.__code__ is renamed)
assert_raises(TypeError, code.replace, co_name=1)
assert_raises(TypeError, code.replace, nope=1)
assert_eq(code.__replace__(co_qualname="Q").co_qualname, "Q")

# Frames: a generator keeps one frame, which reports where it resumes and,
# once finished, where it ended; trace settings are stored; clear() drops
# the locals of a finished frame and refuses an executing or suspended one.
def stepper(a):
    b = a + 1
    yield b
    yield b
gen = stepper(1)
frame = gen.gi_frame
assert_true(frame is gen.gi_frame and frame.f_generator is gen)
next(gen)
assert_eq((frame.f_lineno, sorted(frame.f_locals)), (stepper.__code__.co_firstlineno + 2, ["a", "b"]))
assert_raises(RuntimeError, frame.clear)
list(gen)
assert_eq((frame.f_lineno, frame.f_generator, gen.gi_frame), (stepper.__code__.co_firstlineno + 3, None, None))
def finished(v):
    def inner():
        return v
    w = inner()
    try:
        raise KeyError
    except KeyError as error:
        return error.__traceback__.tb_frame
frame = finished(1)
frame.f_trace = len
frame.f_trace_lines = False
assert_eq((frame.f_trace, frame.f_trace_lines, frame.f_trace_opcodes, type(frame.f_lasti)), (len, False, False, int))
assert_raises(TypeError, setattr, frame, "f_trace_lines", 1)
assert_raises(ValueError, setattr, frame, "f_lineno", 1)
assert_raises(AttributeError, setattr, frame, "f_code", None)
frame.clear()
assert_eq(dict(frame.f_locals), {})

# Traceback and slice attributes are read-only; a slice checks its step
# (type, then zero) before its bounds.
try:
    raise KeyError
except KeyError as error:
    traceback = error.__traceback__
for target, name in [(traceback, "tb_frame"), (traceback, "tb_lasti"), (slice(1), "start"), (slice(1), "step")]:
    try:
        setattr(target, name, None)
    except AttributeError as error:
        assert_eq(str(error), "readonly attribute")
try:
    slice("a").indices(3)
except TypeError as error:
    assert_eq(str(error), "slice indices must be integers or None or have an __index__ method")
try:
    [1, 2]["a":]
except TypeError as error:
    assert_eq(str(error), "slice indices must be integers or have an __index__ method")
assert_raises(ValueError, slice("a", None, 0).indices, 3)

# A classmethod object binds any callable as a method object; static and
# class method objects copy only the callable's naming attributes, and read
# its annotations on demand.
class Binder:
    absolute = classmethod(abs)
bound = Binder.absolute
assert_eq((type(bound).__name__, bound.__func__ is abs, bound.__self__ is Binder), ("method", True, True))
assert_true(repr(type(bound)(len, [1])).startswith("<bound method len of [1]"))
def annotated(a: int): pass
wrapped = staticmethod(annotated)
assert_eq(sorted(wrapped.__dict__), ["__doc__", "__module__", "__name__", "__qualname__"])
assert_eq(wrapped.__annotations__, {"a": int})
assert_true("__annotations__" in wrapped.__dict__)
