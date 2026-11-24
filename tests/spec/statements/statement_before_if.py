# spec: PLS-315 18.2.2
# description: A pass, break or continue statement followed by a
#   conditional expression's if and else is a statement given where an
#   expression is expected.
from harness import *

def check(source, start, end, message="expected expression before 'if', but statement is given"):
    caught = assert_syntax_error(source)
    assert_eq(caught.msg, message, source)
    assert_eq((caught.lineno, caught.offset, caught.end_lineno, caught.end_offset), (1, start, 1, end), source)

check("pass if 1 else x\n", 1, 5)
check("break if a else b\n", 1, 6)
check("continue if a else b\n", 1, 9)
check("x = 1; pass if a else b\n", 8, 12)
check("x = pass if 1 else x\n", 5, 9)
check("x = 1 if 2 else pass\n", 17, 21, "expected expression after 'else', but statement is given")
# Without the else, it is a statement followed by invalid syntax.
assert_eq(assert_syntax_error("pass if 1\n").msg, "invalid syntax")
