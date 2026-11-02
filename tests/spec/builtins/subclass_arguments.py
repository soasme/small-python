# spec: PLS-315 5.2.7, 10.4.2, 19.3.16, 19.3.21, 19.3.22, 21.4.1, 22.3, 22.4.1, 23.1.4, 23.3.1, 23.6, 24.1.3
# description: subclass instances meet builtin type requirements: str names, encodings, format specs, translation tables, complex text and hex separators; tuple class and prefix choices and bases; dict subclass mappings.
from harness import *


class S(str):
    pass


class B(bytes):
    pass


# A class or function name may be a str subclass instance, kept as given.
class C:
    pass
C.__name__ = S("Z")
C.__qualname__ = S("Q")
assert_type(C.__name__, S)
assert_eq(repr(C), f"<class '{__name__}.Q'>")
assert_eq(str(assert_raises(TypeError, C, 1)), "Z() takes no arguments")
T = type(S("N"), (), {})
assert_type(T.__name__, S)
assert_type(T.__qualname__, S)
assert_type(type("N", (), {"__qualname__": S("Q")}).__qualname__, S)
assert_eq(str(assert_raises(TypeError, type, "N", (), {"__qualname__": object()})), "type __qualname__ must be a str, not object")
assert_eq(__build_class__(lambda: None, S("Built")).__name__, "Built")
def f(a):
    pass
f.__qualname__ = S("g")
assert_eq(str(assert_raises(TypeError, f)), "g() missing 1 required positional argument: 'a'")
assert_true(repr(f).startswith("<function g at "))

# Exception group messages.
group = ExceptionGroup(S("msg"), [ValueError(1)])
assert_type(group.message, S)
assert_eq(str(group), "msg (1 sub-exception)")

# Encodings and error handler names.
assert_eq("a".encode(S("ascii"), S("strict")), b"a")
assert_eq(b"a".decode(S("ascii")), "a")
assert_eq(bytes(S("a"), "ascii"), b"a")
assert_eq(bytearray(S("a"), S("ascii"), S("strict")), bytearray(b"a"))
assert_eq(str(b"a", S("ascii")), "a")
assert_eq(str(assert_raises(LookupError, "a".encode, S("bogus"))), "unknown encoding: bogus")
assert_eq("a".encode("ascii", S("bogus")), b"a")
assert_eq(str(assert_raises(LookupError, "\xff".encode, "ascii", S("bogus"))), "unknown error handler name 'bogus'")
assert_eq(str(assert_raises(TypeError, bytes, S("a"))), "string argument without an encoding")
assert_eq(str(assert_raises(TypeError, bytearray, S("a"))), "string argument without an encoding")
assert_eq(str(assert_raises(TypeError, bytes, 1, S("x"))), "encoding without a string argument")
assert_eq(str(assert_raises(TypeError, bytes, 1, 5)), "bytes() argument 'encoding' must be str, not int")
assert_eq(str(assert_raises(TypeError, int.from_bytes, S("ab"))), "cannot convert 'S' object to bytes")
class WithBytes(str):
    def __bytes__(self):
        return b"zz"
assert_eq(bytes(WithBytes("a")), b"zz")
assert_eq(str(assert_raises(TypeError, bytearray, WithBytes("a"))), "string argument without an encoding")

# Format specifications: builtin formatting reads the text, __format__ gets the object.
class Spec:
    def __format__(self, spec):
        return type(spec).__name__ + ":" + spec
assert_eq(format(5, S("03d")), "005")
assert_eq(format(1.5, S(".2f")), "1.50")
assert_eq(format("ab", S(">4")), "  ab")
assert_eq(format(Spec(), S("x")), "S:x")
assert_eq(str(assert_raises(ValueError, format, 5, S("q"))), "Unknown format code 'q' for object of type 'int'")

# Translation tables and containment.
assert_eq(str.maketrans(S("ab"), S("cd"), S("e")), {97: 99, 98: 100, 101: None})
assert_eq(str.maketrans({S("a"): "b"}), {97: "b"})
assert_eq(str(assert_raises(TypeError, str.maketrans, type("D", (dict,), {})(a=1))), "if you give only one argument to maketrans it must be a dict")
assert_eq("abc".translate({97: S("z")}), "zbc")
assert_true(S("b") in "abc")

# complex() parses the text of a str subclass.
assert_eq(complex(S("1+2j")), 1 + 2j)
assert_eq(str(assert_raises(TypeError, complex, S("1"), 2)), "complex() argument 'real' must be a real number, not S")

# hex separators are checked by length, then type; fromhex takes any bytes-like object.
assert_eq(b"ab".hex(S(":")), "61:62")
assert_eq(b"ab".hex(B(b"-")), "61-62")
assert_eq(str(assert_raises(TypeError, b"ab".hex, bytearray(b"-"))), "sep must be str or bytes.")
assert_eq(str(assert_raises(TypeError, b"ab".hex, [1])), "sep must be str or bytes.")
assert_eq(str(assert_raises(ValueError, b"ab".hex, [1, 2])), "sep must be length 1.")
assert_eq(str(assert_raises(TypeError, b"ab".hex, 5)), "object of type 'int' has no len()")
assert_eq(bytes.fromhex(S("61 62")), b"ab")
assert_eq(bytes.fromhex(memoryview(b"6162")), b"ab")
assert_eq(bytearray.fromhex(B(b"61")), bytearray(b"a"))

# float.fromhex reads a str subclass's text.
assert_eq(float.fromhex(S("0x1p1")), 2.0)

# A tuple subclass is a tuple of choices, searched by its items.
class Choices(tuple):
    def __iter__(self):
        raise AssertionError("the items are read directly")
assert_true(isinstance(1, Choices((str, int))))
assert_true(issubclass(bool, Choices((int,))))
assert_true("abc".startswith(Choices(("x", "a"))))
assert_true("abc".endswith(Choices(("c",))))
assert_true(b"abc".startswith(Choices((b"a",))))
assert_eq(str(assert_raises(TypeError, "abc".startswith, Choices((1,)))), "tuple for startswith must only contain str, not int")
assert_eq(type("X", Choices((object,)), {}).__bases__, (object,))

# A dict subclass is a mapping for %-formatting.
class Mapping(dict):
    pass
assert_eq("%(a)s-%(b)d" % Mapping(a="x", b=2), "x-2")
assert_eq(b"%(a)s" % Mapping({b"a": b"y"}), b"y")
