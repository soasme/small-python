# spec: PLS-315 23.6
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
