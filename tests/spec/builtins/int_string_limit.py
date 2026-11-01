# spec: PLS-315 22.1.8
# description: The integer string conversion limit on decimal text, both ways, and the bases and conversions it leaves alone.
from harness import *

limit = host.int_max_str_digits()
use = host.name("the int string limit")
too_long = 10 ** limit
assert_eq(len(str(too_long - 1)), limit)

def check(error, message, function, *args):
    assert_eq(str(assert_raises(error, function, *args)), message)

# Converting to decimal text.
written = f"Exceeds the limit ({limit} digits) for integer string conversion; use {use} to increase the limit"
for convert in (str, repr, lambda n: format(n, "d"), lambda n: f"{n:,}", lambda n: "%d" % n, lambda n: "%i" % -n, lambda n: "%u" % n):
    check(ValueError, written, convert, too_long)

# Parsing decimal text: signs, underscores and white space are not counted.
read = f"Exceeds the limit ({limit} digits) for integer string conversion: value has {limit + 1} digits; use {use} to increase the limit"
check(ValueError, read, int, "1" * (limit + 1))
check(ValueError, read, int, " -" + "1_" * limit + "1 ")
check(ValueError, read, int, "1" * (limit + 1), 7)
assert_eq(int(" +" + "9" * limit + " "), too_long - 1)
literal = assert_raises(SyntaxError, compile, "x = " + "1" * (limit + 1), "<spec>", "exec")
assert_eq(literal.msg, read + " - Consider hexadecimal for huge integer literals to avoid decimal conversion limits.")

# Bases that are powers of two, and float conversions, are unaffected.
assert_eq(int(hex(too_long), 16), too_long)
assert_eq(int(format(too_long, "o"), 8), too_long)
assert_eq(int("1" * (4 * limit), 2).bit_length(), 4 * limit)
assert_eq(float("1" * (limit + 1)), float("1" * (limit + 1) + ".0"))
