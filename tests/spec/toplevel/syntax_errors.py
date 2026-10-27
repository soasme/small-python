# spec: reference/toplevel_components.html
# description: Invalid programs raise SyntaxError with the right message and position.
from harness import *

src = """
def valid_func():
    pass

yield 2
"""

with assert_raises(SyntaxError) as ae:
    compile(src, 'test.py', 'exec')
assert ae.exception.lineno == 5

src = """
if True:
pass
"""

with assert_raises(IndentationError):
    compile(src, '', 'exec')

src = """
if True:
  pass
    pass
"""

with assert_raises(IndentationError):
    compile(src, '', 'exec')

src = """
if True:
    pass
  pass
"""

with assert_raises(IndentationError):
    compile(src, '', 'exec')

src = """
if True:
    pass
\tpass
"""

with assert_raises(TabError):
    compile(src, '', 'exec')

with assert_raises(SyntaxError):
    compile('0xX', 'test.py', 'exec')


src = """
"aaaa" \a
"bbbb"
"""

with assert_raises(SyntaxError):
    compile(src, 'test.py', 'exec')

src = """
from __future__ import not_a_real_future_feature
"""

with assert_raises(SyntaxError):
    compile(src, 'test.py', 'exec')

src = """
a = 1
from __future__ import print_function
"""

with assert_raises(SyntaxError):
    compile(src, 'test.py', 'exec')

src = """
from __future__ import print_function
"""
compile(src, 'test.py', 'exec')


# CPython reports the unparenthesized `except ... as` error with a range that starts at the
# first exception type and stops just before the `:` closing the clause. `end_offset` is an
# exclusive 1-based *character* column, so that end lands on the column the `:` sits on.
#
# The cases below pin the parts that are easy to get wrong: the column counts characters
# rather than UTF-8 bytes, and an explicit line join may sit anywhere between the exception
# types and the `:`. Values verified against CPython 3.14.
except_as_ranges = [
    # (clause, (lineno, offset), (end_lineno, end_offset))
    ("except A, B as e:", (3, 8), (3, 17)),
    ("except A, B as e :", (3, 8), (3, 18)),
    ("except A, B as e   :", (3, 8), (3, 20)),
    ("except A, B as e\t:", (3, 8), (3, 18)),
    ("except A, B, C as blech:", (3, 8), (3, 24)),
    ("except* A, B, C as e:", (3, 9), (3, 21)),
    # A non-ASCII name must not push the column right by its extra UTF-8 bytes.
    ("except Ä, B as e:", (3, 8), (3, 17)),
    ("except 사과, B as e:", (3, 8), (3, 18)),
    ("except A, B as 오:", (3, 8), (3, 17)),
    # An explicit line join may precede or follow `as`, or close the clause on its own line.
    ("except A, B as exc\\\n    :", (3, 8), (4, 5)),
    ("except A, B \\\nas exc:", (3, 8), (4, 7)),
    ("except A, \\\nB as exc:", (3, 8), (4, 9)),
    ("except A, B as \\\nexc:", (3, 8), (4, 4)),
]

for clause, start, end in except_as_ranges:
    src = "try:\n    pass\n%s\n    pass\n" % clause
    with assert_raises(SyntaxError) as ae:
        compile(src, "test.py", "exec")
    exc = ae.exception
    assert exc.msg == "multiple exception types must be parenthesized when using 'as'", (
        clause,
        exc.msg,
    )
    assert (exc.lineno, exc.offset) == start, (clause, (exc.lineno, exc.offset), start)
    assert (exc.end_lineno, exc.end_offset) == end, (
        clause,
        (exc.end_lineno, exc.end_offset),
        end,
    )
# Walrus targets: the first expression of a statement names the bad target,
# a call argument does not.
for source, message in (("x[1] := 2", "cannot use assignment expressions with subscript"),
                        ("(x) := 1", "cannot use assignment expressions with name"),
                        ("f() := 2", "cannot use assignment expressions with function call"),
                        ("a, b := 2", "invalid syntax"),
                        ("print(x.y := 1)", "invalid syntax"),
                        ("[x[1] := 2]", "cannot use assignment expressions with subscript"),
                        ("match 1:\n  case *x: pass", "invalid syntax")):
    assert_eq(assert_syntax_error(source).msg, message)
# A bare except that is not last is a compiler error: parse errors and symbol
# table errors come first.
error = assert_syntax_error("try: pass\nexcept: pass\nexcept ValueError: pass")
assert_eq((error.msg, error.lineno), ("default 'except:' must be last", 2))
assert_eq(assert_syntax_error("try: pass\nexcept: pass\nexcept E: pass\ndef f():\n  nonlocal x").msg,
          "no binding for nonlocal 'x' found")
error = assert_syntax_error("try: pass\nexcept* E: pass\nexcept E: pass")
assert_eq((error.lineno, error.offset), (3, 1))
# Indentation errors carry the tokenizer's columns.
error = assert_syntax_error("x\n    y\n", exception=IndentationError)
assert_eq((error.msg, error.offset, error.end_offset), ("unexpected indent", 4, -1))
error = assert_syntax_error("if 1:\n    x\n  y = 1\n", exception=IndentationError)
assert_eq((error.lineno, error.offset, error.end_offset), (3, 8, -1))
error = assert_syntax_error("a) + 1\n")
assert_eq((error.text, error.offset, error.end_offset), ("a) + 1", 2, 2))
