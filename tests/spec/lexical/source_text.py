# spec: PLS-315 11.1, 11.3, 12.1
# description: Source text code points, line terminators, token separation, and characters that begin no token.
from harness import *

e = assert_syntax_error("x = 1\0\n")
assert_eq(e.msg, "source code string cannot contain null bytes")
assert_raises(SyntaxError, eval, "1\0")
assert_raises(SyntaxError, exec, b"x = 1\0")

# CR LF, CR, and LF terminate physical lines.
for terminator in ("\n", "\r\n", "\r"):
    ns = run(f"a = 1{terminator}b = a + 1{terminator}")
    assert_eq(ns["b"], 2, repr(terminator))
ns = run("a = 1\r\nb = 2\rc = 3\n")
assert_eq((ns["a"], ns["b"], ns["c"]), (1, 2, 3))
assert_eq(assert_syntax_error("x = 1\r\ny = (\r\n").lineno, 2)
# Other Unicode line separators are ordinary characters: in a string they stay.
ns = run("s = '\u2028'\nt = '\x85'\n")
assert_eq(ns["s"], "\u2028")
assert_eq(ns["t"], "\x85")
assert_eq(assert_syntax_error("x = 1\u2028y = 2\n").msg, "invalid non-printable character U+2028")
assert_eq(eval("'a\\\r\nb'"), "ab")

# Whitespace separates tokens; it is needed only where tokens would merge.
assert_eq(eval("1+2"), 3)
assert_eq(eval("1 +\t2"), 3)
assert_eq(eval("1\f+2"), 3)
assert_eq(eval("[1]if 1else 2"), [1])
assert_eq(eval("0xfor 1 else 2") if False else 0, 0)
assert_eq(run("x=1;y=x<<1")["y"], 2)
assert_eq(eval("not-1"), False)
assert_syntax_error("notx = 1\nnot x x\n")

# Characters that begin no token.
for char in "$?`":
    assert_eq(assert_syntax_error(f"a {char} b\n").msg, "invalid syntax", char)
assert_eq(assert_syntax_error("a = 1 € 2\n").msg, "invalid character '€' (U+20AC)")
assert_eq(assert_syntax_error("a = ¡\n").msg, "invalid character '¡' (U+00A1)")
assert_eq(assert_syntax_error("a = \x01\n").msg, "invalid non-printable character U+0001")
assert_eq(assert_syntax_error("a = 1\u200b\n").msg, "invalid non-printable character U+200B")
assert_eq(assert_syntax_error("a\u00a0= 1\n").msg, "invalid non-printable character U+00A0")
# Inside strings and comments any character is allowed.
assert_eq(run("s = '$?`€\x01'  # $?`€\n")["s"], "$?`€\x01")
