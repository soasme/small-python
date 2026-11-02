# spec: PLS-315 23.6, 23.1.8, 24.3
# description: printf-style formatting with str.__mod__.
from harness import *

assert_eq("%s and %r" % ("a", "b"), "a and 'b'")
assert_eq("%d%%" % 50, "50%")
assert_eq("%s" % "single", "single")
assert_eq("%s" % [1, 2], "[1, 2]")
assert_eq("%s" % ((1, 2),), "(1, 2)")
assert_eq("%(name)s is %(age)d" % {"name": "x", "age": 3}, "x is 3")
assert_eq("%(a)s" % {"a": 1, "b": 2}, "1")
assert_eq("%d %i %u" % (1.9, -2.5, True), "1 -2 1")
assert_eq("%o %x %X %#o %#x %#X" % (8, 255, 255, 8, 255, 255), "10 ff FF 0o10 0xff 0XFF")
assert_eq("%.3d|%5.3d" % (7, 7), "007|  007")
assert_eq("%e|%E|%f|%F|%g|%G" % ((1.5,) * 6), "1.500000e+00|1.500000E+00|1.500000|1.500000|1.5|1.5")
assert_eq("%F|%G" % (float("inf"), float("nan")), "INF|NAN")
assert_eq("%.2f %#.0f %#g" % (3.14159, 2.0, 1.5), "3.14 2. 1.50000")
assert_eq("%c%c" % (65, "b"), "Ab")
assert_eq("%a" % "é", "'\\xe9'")
assert_eq("%.2s" % "abcdef", "ab")
assert_eq("[%5d][%-5d][%05d][%+d][% d]" % (42, 42, 42, 42, 42), "[   42][42   ][00042][+42][ 42]")
assert_eq("[%-05d]" % 42, "[42   ]")
assert_eq("[%05s]" % "ab", "[   ab]")
assert_eq("[%*d][%.*f]" % (4, 1, 2, 3.14159), "[   1][3.14]")
assert_eq("%ld %hd %Lf" % (1, 2, 3.0), "1 2 3.000000")
assert_eq("%#06x" % 255, "0x00ff")
assert_eq("%s" % ((),), "()")
assert_eq("no conversions" % (), "no conversions")
assert_eq("%s" % {"a": 1}, "{'a': 1}")

def error(exc, fmt, values):
    return str(assert_raises(exc, lambda: fmt % values))
assert_eq(error(ValueError, "abc%", ()), "stray % at position 3")
assert_eq(error(ValueError, "%y", 1), "unsupported format %y at position 0")
assert_eq(error(ValueError, "ab%-5y", 1), "unsupported format %y at position 2")
assert_eq(error(TypeError, "%(a)s", 1), "format requires a mapping, not int")
assert_eq(error(ValueError, "%(a)s %s", {"a": 1}), "format requires a parenthesised mapping key at position 6")
assert_eq(error(TypeError, "%*d", ("x", 1)), "format argument 1: * requires int, not str")
assert_eq(error(TypeError, "%d %.*f", (1, "x", 1.0)), "format argument 2: * requires int, not str")
assert_eq(error(TypeError, "%s %s", (1,)), "not enough arguments for format string (got 1)")
assert_eq(error(TypeError, "%s", (1, 2)), "not all arguments converted during string formatting (required 1, got 2)")
assert_eq(error(TypeError, "no conversions", 1), "not all arguments converted during string formatting (required 0, got 1)")
assert_eq(error(TypeError, "%d", "x"), "format argument: %d requires a real number, not str")
assert_eq(error(TypeError, "%x", 1.5), "format argument: %x requires an integer, not float")
assert_eq(error(OverflowError, "%c", 0x110000), "format argument: %c argument not in range(0x110000)")
assert_eq(error(TypeError, "%c", "ab"), "format argument: %c requires an integer or a unicode character, not a string of length 2")
# A mapping used without keys is a single argument.
assert_eq("%s" % {"k": 1}, "{'k': 1}")
# %x accepts objects with __index__.
class Index:
    def __index__(self):
        return 255
assert_eq("%x" % Index(), "ff")

# The bytes conversions, and widths and precisions too large to use.
class NotBytes:
    def __bytes__(self): return "s"
assert_eq(str(assert_raises(TypeError, lambda: b"%c" % b"ab")),
          "format argument: %c requires an integer in range(256) or a single byte, not a bytes object of length 2")
assert_eq(str(assert_raises(TypeError, lambda: b"%b" % NotBytes())), "NotBytes.__bytes__() must return a bytes, not str")
assert_eq(str(assert_raises(OverflowError, lambda: "%*d" % (2**63, 1))), "format argument 1: too big for width")
assert_eq(str(assert_raises(OverflowError, lambda: "%.*d" % (2**63, 1))), "format argument 1: too big for precision")
assert_eq(str(assert_raises(ValueError, lambda: "%99999999999999999999d" % 1)), "width too big at position 0")
assert_eq(str(assert_raises(ValueError, lambda: "%.99999999999999999999d" % 1)), "precision too big at position 0")

# str.__mod__ formats whatever the values are, so its errors propagate;
# __rmod__ formats a template of its own type and declines anything else.
assert_raises(TypeError, "x".__mod__, 1, message="not all arguments converted during string formatting (required 0, got 1)")
assert_eq("%s".__mod__(None), "None")
assert_eq("x".__rmod__("<%s>"), "<x>")
assert_raises(TypeError, "x".__rmod__, "y", message="not all arguments converted during string formatting (required 0, got 1)")
assert_is("x".__rmod__(1), NotImplemented)
assert_is("x".__rmod__(b"%s"), NotImplemented)
assert_eq(b"x".__rmod__(b"<%s>"), b"<x>")
assert_is(b"x".__rmod__(bytearray(b"%s")), NotImplemented)
assert_eq(bytearray(b"%d").__mod__(5), bytearray(b"5"))
class Rmod(str):
    def __rmod__(self, other):
        return "reflected"
assert_eq("%s" % Rmod("v"), "reflected")
assert_eq("%s".__mod__(Rmod("v")), "v")

# Conversion errors name the argument's fully qualified type.
def make_local():
    class Local: pass
    return Local()
local = make_local()
for fmt, args, wanted in (("%x", local, "%x requires an integer"), ("%d", local, "%d requires a real number"),
                          ("%f", local, "%f requires a real number"), ("%c", local, "%c requires an integer or a unicode character"),
                          ("%*d", (local, 1), "* requires int"),
                          (b"%x", local, "%x requires an integer"), (b"%c", local, "%c requires an integer in range(256) or a single byte"),
                          (b"%b", local, "%b requires a bytes-like object, or an object that implements __bytes__")):
    position = "format argument 1" if fmt in ("%*d",) else "format argument"
    e = assert_raises(TypeError, lambda: fmt % args)
    assert_eq(str(e), f"{position}: {wanted}, not make_local.<locals>.Local")
