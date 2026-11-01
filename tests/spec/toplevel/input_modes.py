# spec: PLS-315 17.6, 12.3
# description: Expression and interactive input end without a newline; empty input and a trailing ';' fail at the end marker.
from harness import *

def error(source, mode):
    try: compile(source, "s", mode)
    except SyntaxError as e: return type(e).__name__, e.msg, e.args[1]
    return None

for mode in ("eval", "single"):
    for source, line in (("", 0), ("\n", 1), ("\n\n", 2), ("# c", 1), ("# c\n", 1), (" # c", 1)):
        text = source.split("\n")[line - 1] + "\n" * (source.count("\n") >= line) if line else ""
        assert_eq(error(source, mode), ("SyntaxError", "invalid syntax", ("s", line, 0, text, line, 0)))
    for source, line, offset, text in ((" ", 1, 1, " "), ("  \t", 1, 3, "  \t"), ("\n ", 2, 1, " ")):
        assert_eq(error(source, mode), ("IndentationError", "unexpected indent", ("s", line, offset, text, line, -1)))
    assert_eq(error(" \n", mode), ("SyntaxError", "invalid syntax", ("s", 1, 0, " \n", 1, 0)))
    assert_eq(error("1 1", mode), ("SyntaxError", "invalid syntax", ("s", 1, 3, "1 1", 1, 4)))
    assert_eq(error("1 1\n\n", mode), ("SyntaxError", "invalid syntax", ("s", 1, 3, "1 1\n", 1, 4)))
    assert_eq(error("if 1:\n  pass\n   ", mode)[:2], ("SyntaxError", "invalid syntax") if mode == "eval" else ("IndentationError", "unexpected indent"))
for source in (" ", "\n\n", "x = 1\n  ", "# c"):
    assert_is(error(source, "exec"), None)

# Interactive input ignores a final line of blanks after its statement.
assert_is(error("1\n ", "single"), None)
assert_is(error("x = 1\n  ", "single"), None)
assert_eq(error("1\n ", "eval"), ("IndentationError", "unexpected indent", ("s", 2, 1, " ", 2, -1)))

# A ';' ends no expression input.
for source, offset in (("1;", 2), ("1;\n", 2), ("1 ;  # x\n", 3)):
    assert_eq(error(source, "eval")[2][1:3], (1, offset))
    assert_is(error(source, "single"), None)
assert_eq(error("1 1", "exec")[2][3], "1 1\n")
assert_eq(eval(" 1"), 1)
assert_raises(SyntaxError, eval, "  \t")
