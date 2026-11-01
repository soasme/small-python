# spec: PLS-315 13.5, 13.7, 13.8, 22.3, 22.4, 24.1.3, 26.1
# description: Shifts and powers of very large integers, complex division by infinities and zero, signed zeros of float remainders, and the fromhex and fromkeys class methods.
from harness import *

huge = 1 << 70
assert_eq((1 << 10**6) >> huge, 0)
assert_eq(0 << huge, 0)
assert_eq(-5 >> huge, -1)
assert_raises(OverflowError, lambda: 5 << huge, message="too many digits in integer")
assert_eq(-(1 << 100) >> 3, -(1 << 97))
assert_eq((-(1 << 100) - 7) >> 3, -(1 << 97) - 1)

assert_eq((1 << 100) ** -1, 2.0 ** -100)
assert_raises(ZeroDivisionError, lambda: 0 ** -(1 << 100), message="zero to a negative power")
assert_eq((-1) ** (1 << 100), 1)
assert_eq((-1) ** ((1 << 100) + 1), -1)
assert_eq(1 ** (1 << 100), 1)

inf, nan = float("inf"), float("nan")
def same(z, real, imag):
    assert_eq(repr(z.real), repr(real))
    assert_eq(repr(z.imag), repr(imag))
same(complex(1, 2) / complex(inf, 0), 0.0, 0.0)
same(complex(inf, 1) / complex(1, 2), inf, -inf)
same(complex(1, 2) / complex(nan, 0), nan, nan)
assert_raises(ZeroDivisionError, lambda: complex(1, 2) / 0j, message="division by zero")
same(1.0 / complex(inf, inf), 0.0, -0.0)
same(inf / complex(1, 1), inf, -inf)

assert_eq(repr(-0.0 % 5.0), "0.0")
assert_eq(repr(0.0 % -5.0), "-0.0")
assert_eq(repr(divmod(-0.0, 5.0)), "(-0.0, 0.0)")

assert_raises(ValueError, bytes.fromhex, "zz", message="non-hexadecimal number found in fromhex() arg at position 0")
assert_raises(ValueError, bytes.fromhex, "0", message="fromhex() arg must contain an even number of hexadecimal digits")
assert_raises(ValueError, bytes.fromhex, "a b", message="non-hexadecimal number found in fromhex() arg at position 1")
assert_eq(bytes.fromhex(" 0a 0b "), b"\n\x0b")
assert_eq(bytes.fromhex(b"0a"), b"\n")
assert_raises(TypeError, bytes.fromhex, 1, message="fromhex() argument must be str or bytes-like, not int")
assert_raises(OverflowError, float.fromhex, "0x1p+5000", message="hexadecimal value too large to represent as a float")
assert_eq(repr(float.fromhex("0x1.8p-1080")), "0.0")
assert_eq(repr(float.fromhex("-0x1p-1075")), "-0.0")

assert_raises(TypeError, dict.fromkeys, 1, message="'int' object is not iterable")
assert_eq(dict.fromkeys([1, 2], 0), {1: 0, 2: 0})
assert_eq(dict.fromkeys({1: 2}, 0), {1: 0})
assert_eq(dict.fromkeys({1, 2}), {1: None, 2: None})
assert_eq(dict.fromkeys("ab"), {"a": None, "b": None})
class Dict(dict): pass
made = Dict.fromkeys({1: 2})
assert_eq(type(made), Dict)
assert_eq(made, {1: None})
