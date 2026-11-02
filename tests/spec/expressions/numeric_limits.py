# spec: PLS-315 13.5, 13.7, 13.8, 22.1.9, 22.3, 22.3.2, 22.3.5, 22.4, 24.1.3, 26.1
# description: Shifts and powers of very large integers, float powers of zeros, infinities and NaNs, complex division by infinities and zero, signed zeros of float remainders, NaN hashes of subclass instances, and the fromhex and fromkeys class methods.
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

# An infinite or NaN operand takes IEEE pow's special cases first.
assert_eq(repr(0.0 ** -inf), "inf")
assert_eq(repr(-0.0 ** -inf), "-inf")
assert_eq(repr((-2.0) ** nan), "nan")
assert_eq(repr((-inf) ** 0.5), "inf")
assert_eq(repr((-inf) ** -0.5), "0.0")
assert_raises(ZeroDivisionError, lambda: 0.0 ** -0.5, message="zero to a negative power")
assert_eq(repr((-8.0) ** (1 / 3)), repr(complex(-8.0) ** (1 / 3)))

# A NaN hashes by the identity of the object holding it.
class Float(float): pass
class Complex(complex): pass
for number in (nan, Float(nan)):
    assert_eq(hash(number), object.__hash__(number))
number = Complex(1, nan)
mixed = (1 + 1000003 * object.__hash__(number)) % 2**64
assert_eq(hash(number), mixed - 2**64 if mixed >= 2**63 else mixed)
assert_eq(hash(Float(1.5)), hash(1.5))
assert_eq(hash(Complex(1, 2)), hash(1 + 2j))

assert_raises(ValueError, bytes.fromhex, "zz", message="non-hexadecimal number found in fromhex() arg at position 0")
assert_raises(ValueError, bytes.fromhex, "0", message="fromhex() arg must contain an even number of hexadecimal digits")
assert_raises(ValueError, bytes.fromhex, "a b", message="non-hexadecimal number found in fromhex() arg at position 1")
assert_eq(bytes.fromhex(" 0a 0b "), b"\n\x0b")
assert_eq(bytes.fromhex(b"0a"), b"\n")
assert_raises(TypeError, bytes.fromhex, 1, message="fromhex() argument must be str or bytes-like, not int")
assert_raises(OverflowError, float.fromhex, "0x1p+5000", message="hexadecimal value too large to represent as a float")
assert_eq(repr(float.fromhex("0x1.8p-1080")), "0.0")
assert_eq(repr(float.fromhex("-0x1p-1075")), "-0.0")
# fromhex rounds once, half to even, to the precision of the result; digits
# past any bit the result keeps still decide a tie.
assert_eq(float.fromhex("0x0.ffffffffffffd6p-1022").hex(), "0x0.ffffffffffffdp-1022")
assert_eq(float.fromhex("0x0.ffffffffffffd8p-1022").hex(), "0x0.ffffffffffffep-1022")
assert_eq(float.fromhex("0x0.ffffffffffffe8p-1022").hex(), "0x0.ffffffffffffep-1022")
assert_eq(float.fromhex("0x0.fffffffffffff8p-1022").hex(), "0x1.0000000000000p-1022")
assert_eq(float.fromhex("0x1p-1075").hex(), "0x0.0p+0")
assert_eq(float.fromhex("0x1.00000000000000001p-1075").hex(), "0x0.0000000000001p-1022")
assert_eq(float.fromhex("0x1p-1076").hex(), "0x0.0p+0")
assert_eq(float.fromhex("0x1.00000000000008000000000000000001p0").hex(), "0x1.0000000000001p+0")
assert_eq(float.fromhex("0x1.00000000000008p0").hex(), "0x1.0000000000000p+0")
assert_eq(float.fromhex("0x10000000000000800000000000000001").hex(), "0x1.0000000000001p+124")
assert_eq(float.fromhex("0x0.0000000000000000000000000001p0").hex(), "0x1.0000000000000p-112")
assert_raises(OverflowError, float.fromhex, "0x1.fffffffffffff8p1023", message="hexadecimal value too large to represent as a float")
assert_eq(float.fromhex("0x1.fffffffffffff7ffp1023").hex(), "0x1.fffffffffffffp+1023")

assert_raises(TypeError, dict.fromkeys, 1, message="'int' object is not iterable")
assert_eq(dict.fromkeys([1, 2], 0), {1: 0, 2: 0})
assert_eq(dict.fromkeys({1: 2}, 0), {1: 0})
assert_eq(dict.fromkeys({1, 2}), {1: None, 2: None})
assert_eq(dict.fromkeys("ab"), {"a": None, "b": None})
class Dict(dict): pass
made = Dict.fromkeys({1: 2})
assert_eq(type(made), Dict)
assert_eq(made, {1: None})
