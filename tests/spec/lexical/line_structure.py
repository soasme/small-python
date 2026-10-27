# spec: reference/lexical_analysis.html#line-structure
# description: Logical lines, explicit and implicit joining, blank lines, comments.
from harness import *

# Explicit line joining with a backslash.
x = 1 + \
    2
assert_eq(x, 3)
if 1 == 1 and \
   2 == 2:
    joined = True
assert_true(joined)

# A backslash does not continue a comment, and cannot follow a comment.
assert_syntax_error("x = 1 + # comment \\\n2\n")
# A line ending in a backslash cannot carry a token after it.
assert_syntax_error("x = 1 \\ 2\n")
# Backslash outside a string literal and not at the end of a line.
assert_syntax_error("a = \\ b\n")

# Implicit line joining inside brackets, with comments and odd indentation.
month_names = ['Januari', 'Februari', 'Maart',      # These are the
               'April',   'Mei',      'Juni',       # Dutch names
        'Juli',    'Augustus', 'September',  # for the months
                       'Oktober', 'November', 'December']   # of the year
assert_eq(len(month_names), 12)
assert_eq(len({1,
    2,
                3}), 3)
assert_eq(f(1,
  2) if (f := lambda a, b: a + b) else None, 3)

# Blank lines and comment-only lines are ignored.
ns = run("\n\n# only a comment\n   \n\t\nx = 1\n\n   # indented comment\ny = 2\n")
assert_eq((ns["x"], ns["y"]), (1, 2))

# Source may end without a newline, with \r\n or \r line endings.
assert_eq(run("a = 1")["a"], 1)
assert_eq(run("a = 1\r\nb = 2\r\n")["b"], 2)
assert_eq(run("a = 1\rb = 2\r")["b"], 2)
assert_eq(run("if 1:\r\n    a = 5\r\n")["a"], 5)

# Several statements on one logical line.
a = 1; b = 2; c = a + b;
assert_eq(c, 3)
assert_syntax_error("a = 1;;\n")
assert_syntax_error(";\n")

# A form feed at the start of a line is ignored for indentation.
assert_eq(run("if 1:\n\f    a = 7\n")["a"], 7)
assert_eq(run("\fa = 8\n")["a"], 8)
