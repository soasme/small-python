# spec: PLS-315 12, 11.2
# description: A lexical error later in the source replaces a parser's SyntaxError, except inside an f-string, at an unexpected indent, or when it only ends the token stream.
from harness import *


def check(source, exception, message, lineno):
    error = assert_syntax_error(source, exception=exception)
    assert_eq((type(error), error.msg, error.lineno), (exception, message, lineno), repr(source))


# The parser fails on line 1; the tokenizer still reads on.
check("'a' b\n'c", SyntaxError, "unterminated string literal (detected at line 2)", 2)
check("x y\n1_", SyntaxError, "invalid decimal literal", 2)
# The parser's own messages are replaced too, an IndentationError among them.
check("if x:\npass\n'c", SyntaxError, "unterminated string literal (detected at line 3)", 3)
# A lexical error inside an f-string leaves the parser's error.
check("x y\nf'{1'", SyntaxError, "invalid syntax", 1)
# A bracket left open after the failing line is no lexical error.
check("x y\n(", SyntaxError, "invalid syntax", 1)
# Errors that only end the token stream leave the parser's error.
check("x y\n  1\n z", SyntaxError, "invalid syntax", 1)
check("x y\n1 \\ 2", SyntaxError, "invalid syntax", 1)
check("if 0:\n if 0:\n if 0:\n\tif 0:\n", IndentationError,
      "expected an indented block after 'if' statement on line 2", 3)
# A parser that reads to the end inside a bracket reports the bracket.
check("f(1 for c in I,\n", SyntaxError, "'(' was never closed", 1)
# Undecodable bytes are a lexical error located at the first invalid byte (11.2).
error = assert_syntax_error(b"x = 1\ny = '\xc3'")
assert_eq((error.lineno, error.offset, error.text), (2, 6, "y = '\ufffd'"))
assert_true(error.msg.startswith("Non-UTF-8 code starting with '\\xc3' on line 2, but no encoding declared"))
