# spec: PLS-315 22.4.1
# description: complex() of a string: underscores, parentheses, white space, and the two error messages.
from harness import *

assert_eq(complex("1_2j"), 12j)
assert_eq(complex("1_2_3+4_5j"), 123 + 45j)
assert_eq(complex("(1_2j)"), 12j)
assert_eq(complex("1.0_1j"), 1.01j)
assert_eq(complex(" ( 1+2j ) "), 1 + 2j)
assert_eq(complex("-j"), -1j)
assert_eq(complex("1e1_0j"), 1e10j)
# An underscore not between two digits: "could not convert", with the repr.
for text in ("_1j", "1_", "1__2j", " 1__2j", "x_y", "1_j", "1._5"):
    e = assert_raises(ValueError, complex, text)
    assert_eq(str(e), f"could not convert string to complex: {text!r}")
# Any other malformed text.
for text in ("", " ", "x", "1+", "(1", "1j)", "1e", "j1", "+-1", "1+2", "1 + 2j", "()"):
    e = assert_raises(ValueError, complex, text)
    assert_eq(str(e), "complex() arg is a malformed string")
