# spec: PLS-315 23.2, 23.1.7
# description: The Unicode character properties behind the str classification methods.
from harness import *

# alphabetic: L* categories.
for ch in "aZéω中ʰǅ":
    assert_true(ch.isalpha(), repr(ch))
for ch in "1 _٠Ⅰ":
    assert_false(ch.isalpha(), repr(ch))
# decimal: Nd; digit: Numeric_Type Decimal or Digit; numeric: also Numeric.
assert_eq([c.isdecimal() for c in "7٣²⅕Ⅰ"], [True, True, False, False, False])
assert_eq([c.isdigit() for c in "7٣²⅕Ⅰ"], [True, True, True, False, False])
assert_eq([c.isnumeric() for c in "7٣²⅕Ⅰ一"], [True, True, True, True, True, True])
assert_false("a".isnumeric())
# white space: bidi WS, B, S, or Zs.
for ch in " \t\n\r\x0b\x0c\x1c\x1d\x1e\x1f\x85\xa0    　":
    assert_true(ch.isspace(), repr(ch))
for ch in "​\x00a᠎":
    assert_false(ch.isspace(), repr(ch))
# printable: not Cc, Cf, Cs, Co, Cn, Zl, Zp, Zs, except the space.
assert_eq([c.isprintable() for c in " aé"], [True, True, True])
assert_eq([c.isprintable() for c in "\n\x7f­​ 　\U000e0001"], [False] * 8)
assert_true("".isprintable())
# cased, upper, lower, title.
assert_true("ǅ".istitle())
assert_false("ǅ".isupper())
assert_false("ǅ".islower())
assert_true("ª".islower())       # Other_Lowercase
assert_true("Ⅰ".isupper())       # Other_Uppercase: ROMAN NUMERAL ONE
assert_false("1".isupper())
assert_true("A1".isupper())
assert_false("".islower())
# The decimal value: StringToInt and StringToFloat accept any Nd digit.
assert_eq(int("٣١"), 31)
assert_eq(int("１２"), 12)
assert_eq(float("١.٥"), 1.5)
assert_raises(ValueError, int, "²")
assert_raises(ValueError, int, "⅕")
