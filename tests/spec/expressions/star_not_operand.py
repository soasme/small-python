# spec: PLS-315 13.15, 13.11
# description: a starred item's bitwise-or operand cannot begin with not,
# invalid syntax at the not, while a call's starred argument takes any
# expression; a parenthesized starred item that reads further as an
# expression than as a bitwise or is invalid syntax where it stops. A not
# after an arithmetic operator, or after a unary operator that begins a
# term, must be parenthesized; after any other operator it is invalid syntax.
from harness import *
a, b = 1, 1

for source, message, at, end in [("[*not a]", "invalid syntax", 3, 6), ("x = *not a", "invalid syntax", 6, 9), ("(b, *not a)", "invalid syntax", 6, 9),
                                 ("{*not a}", "invalid syntax", 3, 6), ("x = a, *not b", "invalid syntax", 9, 12),
                                 ("(*not a, b)", "invalid syntax", 8, 9), ("(*a or b, b)", "invalid syntax", 9, 10), ("(*a < b, b)", "invalid syntax", 8, 9),
                                 ("(*lambda: 0, b)", "invalid syntax", 12, 13), ("(*a or b c)", "invalid syntax. Perhaps you forgot a comma?", 3, 11),
                                 ("(*lambda: 0 b)", "invalid syntax. Perhaps you forgot a comma?", 11, 14), ("(*a b)", "invalid syntax. Perhaps you forgot a comma?", 3, 6)]:
    caught = assert_syntax_error(source)
    assert_eq((caught.msg, caught.offset, caught.end_offset), (message, at, end), source)
for source, message, at, end in [("a + not b", "'not' after an operator must be parenthesized", 5, 10), ("a @ not b", "'not' after an operator must be parenthesized", 5, 10),
                                 ("a // not b", "'not' after an operator must be parenthesized", 6, 11), ("-not x", "'not' after an operator must be parenthesized", 2, 7),
                                 ("a < -not b", "'not' after an operator must be parenthesized", 6, 11), ("a < not b", "invalid syntax", 5, 8),
                                 ("a | not b", "invalid syntax", 5, 8), ("a << not b", "invalid syntax", 6, 9), ("2 ** not x", "invalid syntax", 6, 9),
                                 ("a ** -not b", "invalid syntax", 7, 10), ("a in not b", "invalid syntax", 6, 9), ("a is not not b", "invalid syntax", 10, 13)]:
    caught = assert_syntax_error(source)
    assert_eq((caught.msg, caught.offset, caught.end_offset), (message, at, end), source)
assert_eq([a and not b, not not a, -a < -(not b)], [False, True, True])
def f(*a): return a
assert_eq(str(assert_raises(TypeError, lambda: f(*not []))), "Value after * must be an iterable, not bool")
assert_eq(f(*[] or [1], *not [] and [2]), (1, 2))
