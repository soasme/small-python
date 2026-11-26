# spec: PLS-315 15.6.1
# description: a name bound twice in a case pattern is reported at the
# pattern binding it again (its capture, starred or as pattern, or the
# mapping pattern of a ** rest); alternatives binding different names at
# their or-pattern; two starred names at their sequence pattern, brackets
# included; each with its end column.
from harness import *

def located(pattern):
    error = assert_syntax_error("match x:\n    case %s: pass" % pattern)
    return error.msg, error.offset, error.end_offset

for pattern, name, place in (("[b, 1 as b]", "b", (14, 20)), ("[b, *b]", "b", (14, 16)), ("[*b, b]", "b", (15, 16)),
                             ("{1: b, **b}", "b", (10, 21)), ("[{1: b, **b}]", "b", (11, 22)), ("C(b, k=[b])", "b", (18, 19)),
                             ("C(x=b, y=b)", "b", (19, 20)), ("b as b", "b", (10, 16)), ("[x, (y, x)]", "x", (18, 19))):
    assert_eq(located(pattern), ("multiple assignments to name '%s' in pattern" % name, *place), pattern)
assert_eq(located("{**__debug__}"), ("cannot assign to __debug__", 10, 23))
assert_eq(located("[a, b] | [a]"), ("alternative patterns bind different names", 10, 22))
assert_eq(located("1 | a"), ("alternative patterns bind different names", 10, 15))
assert_eq(located("(a | b)"), ("name capture 'a' makes remaining patterns unreachable", 11, 12))
for pattern, place in (("[*a, *b]", (10, 18)), ("(*a, *b,)", (10, 19)), ("*a, *b", (10, 16)), ("[1, [*a, *b]]", (14, 22))):
    assert_eq(located(pattern), ("multiple starred names in sequence pattern", *place), pattern)
