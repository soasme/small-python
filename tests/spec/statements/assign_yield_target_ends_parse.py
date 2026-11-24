# spec: PLS-315 14.2.2
# description: An assignment to a yield expression is an error at that
#   yield, found before the parse reads past the '=' after it.
from harness import *

def check(source, start, end):
    caught = assert_syntax_error(source)
    assert_eq(caught.msg, "assignment to yield expression not possible", source)
    assert_eq((caught.offset, caught.end_offset), (start, end), source)

check("def f():\n x = yield = 1\n", 6, 11)
check("def f():\n yield = 1\n", 2, 7)
check("def f():\n x = yield = y = 1\n", 6, 11)
check("def f():\n a, b = yield = 1\n", 9, 14)
# What follows the '=' is not read: neither a syntax error nor a literal
# over the int string limit there is reported.
check("def f():\n x = yield = (\n", 6, 11)
check("def f():\n x = yield = 1 +\n", 6, 11)
check("def f():\n x = yield = 1" + "0" * 5000 + "\n", 6, 11)
