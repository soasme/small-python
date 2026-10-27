# spec: PLS-315 23.4, 7.5.8
# description: str.format and format_map: fields, numbering, attribute and index access, conversions, nesting.
from harness import *

assert_eq("{} {}".format(1, 2), "1 2")
assert_eq("{1} {0} {1}".format("a", "b"), "b a b")
assert_eq("{x}-{y}".format(x=1, y=2), "1-2")
assert_eq("{{}} {{{0}}}".format(5), "{} {5}")
assert_eq("{0.real} {0.imag}".format(3 + 4j), "3.0 4.0")
assert_eq("{0[1]} {0[k]} {1[0][0]}".format({1: "int", "1": "str", "k": "v"}, [[9]]), "int v 9")
assert_eq("{[-1]}".format({"-1": "string key"}), "string key")
assert_eq("{0!r} {0!s} {0!a}".format("é"), "'é' é '\\xe9'")
assert_eq("{:>{width}}|".format("x", width=4), "   x|")
assert_eq("{:.{}f}".format(3.14159, 2), "3.14")
assert_eq("{:{fill}^{w}}".format("m", fill="*", w=5), "**m**")
assert_eq("{0:{1}}".format(7, 3), "  7")

# format_map uses the mapping for names and allows no positional fields.
class Missing(dict):
    def __missing__(self, key):
        return f"<{key}>"
assert_eq("{a} {b}".format_map(Missing(a=1)), "1 <b>")
e = assert_raises(ValueError, "{0}".format_map, {})
assert_eq(str(e), "Format string contains positional fields")

def error(exc, fmt, *args, **kwargs):
    return str(assert_raises(exc, fmt.format, *args, **kwargs))
assert_eq(error(ValueError, "}"), "Single '}' encountered in format string")
assert_eq(error(ValueError, "{"), "Single '{' encountered in format string")
assert_eq(error(ValueError, "{0"), "expected '}' before end of string")
assert_eq(error(ValueError, "{0}{}", 1, 2), "cannot switch from manual field specification to automatic field numbering")
assert_eq(error(ValueError, "{}{0}", 1, 2), "cannot switch from automatic field numbering to manual field specification")
assert_eq(error(IndexError, "{2}", 1), "Replacement index 2 out of range for positional args tuple")
assert_eq(error(IndexError, "{}{}", 1), "Replacement index 1 out of range for positional args tuple")
assert_eq(error(KeyError, "{name}"), "'name'")
assert_eq(error(ValueError, "{0.}", 1), "Empty attribute in format string")
assert_eq(error(AttributeError, "{0.missing}", 1), "'int' object has no attribute 'missing'")
assert_eq(error(ValueError, "{0[0]x}", [1]), "Only '.' or '[' may follow ']' in format field specifier")
assert_eq(error(ValueError, "{0!x}", 1), "Unknown conversion specifier x")
assert_eq(error(ValueError, "{0!rr}", 1), "expected ':' after conversion specifier")
assert_eq(error(ValueError, "{:{:{}}}", 1, 2, 3), "Max string recursion exceeded")
# Brackets are not scanned for braces.
assert_eq("{0[}]}".format({"}": "brace"}), "brace")
# Format calls __format__ with the computed spec.
class Spy:
    def __format__(self, spec):
        return f"<{spec}>"
assert_eq("{0:abc} {0}".format(Spy()), "<abc> <>")
assert_eq("{0!s:>8}".format(Spy()).strip().startswith("<"), True)
assert_eq("{:>3}".format(Spy()), "<>3>")
e = assert_raises(TypeError, format, object(), "x")
assert_eq(str(e), "unsupported format string passed to object.__format__")
