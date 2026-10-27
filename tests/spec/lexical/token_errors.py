# spec: PLS-315 12.2
# description: Stray backslashes and non-printable characters are reported as CPython's tokenizer does.
from harness import *
assert_eq(assert_syntax_error("x = 1 \\ 2").msg, "unexpected character after line continuation character")
assert_eq(assert_syntax_error("x = 1 \\").msg, "unexpected EOF while parsing")
assert_eq(assert_syntax_error("x = (1, \\").msg, "'(' was never closed")
assert_eq(assert_syntax_error("x = 1\x01").msg, "invalid non-printable character U+0001")
assert_eq(assert_syntax_error("x​ = 1").msg, "invalid non-printable character U+200B")
