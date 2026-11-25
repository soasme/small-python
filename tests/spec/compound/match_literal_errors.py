# spec: PLS-315 15.6.2
# description: A complex literal pattern needs a real number on the left of
# + or - and an imaginary number on the right; a right operand that is not a
# number is invalid syntax.
from harness import *

def message(pattern):
    return assert_syntax_error(f"match x:\n    case {pattern}:\n        pass\n").msg

assert_eq([message(p) for p in ("1 + 2", "-1 - 2.5", "1j + 2j", "-1j - 2", "1 +", "1 + a", "1 + -2j", "{1 +: 2}", "-a")],
          ["imaginary number required in complex literal", "imaginary number required in complex literal",
           "real number required in complex literal", "real number required in complex literal",
           "invalid syntax", "invalid syntax", "invalid syntax", "invalid syntax", "invalid syntax"])

match -1.5 + 2j:
    case -1.5 + 2j: matched = True
assert_true(matched)
