# spec: reference/lexical_analysis.html#operators-and-delimiters
# description: The operator and delimiter tokens, and characters that are not tokens.
from harness import *

ops = ["+", "-", "*", "**", "/", "//", "%", "@", "<<", ">>", "&", "|", "^", "~",
       "<", ">", "<=", ">=", "==", "!="]
for op in ops:
    if op == "~":
        assert_compiles("~a")
    else:
        assert_compiles(f"a {op} b")
for aug in ["+=", "-=", "*=", "/=", "//=", "%=", "@=", "&=", "|=", "^=", ">>=", "<<=", "**="]:
    assert_compiles(f"a {aug} b")
assert_compiles("(a := b)")
assert_compiles("def f() -> int: pass")
assert_compiles("x[a:b, ...]")

# '$', '?', and '`' are not tokens outside strings and comments.
for ch in ["$", "?", "`"]:
    assert_syntax_error(f"a {ch} b")
assert_eq("$?`", "$" + "?" + "`")
# '!' only forms '!='.
assert_syntax_error("a ! b")
assert_syntax_error("!a")

# Longest-match tokenization: a**-b is a ** (-b); a//b is floor division.
a, b = 2, 3
assert_eq(a**-b, 0.125)
assert_eq(7//2, 3)
assert_eq(1<<2>>1, 2)
assert_eq(1 if a==2 else 0, 1)
# '<>' is not inequality without barry_as_FLUFL.
assert_syntax_error("1 <> 2")
# Ellipsis literal versus three dots.
assert_is(..., Ellipsis)
assert_syntax_error(". . .")
