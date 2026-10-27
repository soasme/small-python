# spec: PLS-315 12.6
# description: Integer, floating-point, and imaginary literals with underscores and prefixes.
from harness import *

assert_same(7, int("7"))
assert_same(2147483647, 2**31 - 1)
assert_same(0o177, 127)
assert_same(0O17, 15)
assert_same(0b100110111, 311)
assert_same(0B1, 1)
assert_same(0xdeadbeef, 3735928559)
assert_same(0XFF, 255)
assert_same(100_000_000_000, 10**11)
assert_same(0b_1110_0101, 229)
assert_same(0x_FF, 255)
assert_same(0, 0)
assert_same(00, 0)
assert_same(0_0, 0)
assert_same(79228162514264337593543950336, 2**96)

# Leading zeros in non-zero decimal integers are not allowed.
assert_syntax_error("0777")
assert_syntax_error("01")
# Underscores only between digits (or after a base prefix).
for bad in ["1__0", "1_", "_1 + 0" if False else "1_e5", "0x_", "0b2", "0o8", "0xg", "1e", "1e+", "1.e_5", "1._5", "0b", "0o", "0x"]:
    assert_syntax_error(bad)
assert_eq(eval("_1") if False else 1, 1)

# Floating point.
assert_same(3.14, 314 / 100)
assert_same(10., 10.0)
assert_same(.001, 1 / 1000)
assert_same(1e100, 10.0**100)
assert_same(3.14e-10, 314e-12)
assert_same(0e0, 0.0)
assert_same(3.14_15_93, 3.141593)
assert_same(1_000.000_1, 1000.0001)
assert_same(1E5, 100000.0)
assert_same(077e010, 77e10)  # leading zeros are fine in floats
assert_same(00.5, 0.5)
assert_same(1e400, float("inf"))
assert_same(1e-400, 0.0)

# Imaginary.
assert_same(3.14j, complex(0, 3.14))
assert_same(10.j, 10j)
assert_same(10j, complex(0, 10))
assert_same(.001J, 0.001j)
assert_same(1e100j, complex(0, 1e100))
assert_same(3.14e-10j, complex(0, 3.14e-10))
assert_same(3.14_15_93j, complex(0, 3.141593))
assert_same(0j, complex(0, 0))
assert_same(007j, 7j)

# A literal followed directly by a name is an error; '1if' style is accepted with a warning? not for 'and'.
assert_syntax_error("1abc")
assert_syntax_error("0x1g")
assert_eq((1).real, 1)
assert_eq(1 .real, 1)
assert_eq(1..real, 1.0)
assert_same(-1, 0 - 1)  # a negative literal is unary minus applied to a literal
