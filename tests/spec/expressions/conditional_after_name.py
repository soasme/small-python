# spec: PLS-315 13.13
# description: the expressions after a name that no "(" follows are read
# as well, so a conditional expression among them without else is its
# error, even after further names; an error inside the first operand so
# read is not reported, and inside brackets two adjacent expressions are a
# missing comma first.
from harness import *

ELSE = "expected 'else' after 'if' expression"
for source, message, at, end in [("a b if c", ELSE, 3, 9), ("a b c if d", ELSE, 5, 11), ("a not b if c", ELSE, 3, 13),
                                 ("x = a b if c", ELSE, 7, 13), ("a, b c if d", ELSE, 6, 12), ("a b or c if d", ELSE, 3, 14),
                                 ("a.b c if d", "invalid syntax", 5, 6), ("1 b if c", "invalid syntax", 3, 4),
                                 ("x f(*)", "invalid syntax", 3, 4), ("a b if c:", "invalid syntax", 3, 4),
                                 ("a b if lambda: 0", "invalid syntax", 3, 4), ("a b c", "invalid syntax", 3, 4),
                                 ("(a b if c)", "invalid syntax. Perhaps you forgot a comma?", 2, 5),
                                 ("f(a b if c)", "invalid syntax. Perhaps you forgot a comma?", 3, 6)]:
    caught = assert_syntax_error(source)
    assert_eq((caught.msg, caught.offset, caught.end_offset), (message, at, end), source)
a = b = 1
assert_eq(a if b else 2, 1)
