# spec: PLS-315 12.5
# description: Quoting, prefixes, triple quotes, escapes, raw strings, concatenation.
from harness import *

assert_eq('abc', "abc")
assert_eq('''a
b''', "a\nb")
assert_eq("""x"y'z""", 'x"y\'z')
assert_eq('it''s', "its")
assert_eq("a" 'b' """c""", "abc")
assert_eq(("a"
           "b"), "ab")

# Prefixes are case-insensitive and combine as the grammar allows.
for prefix in ["r", "R", "u", "U", "b", "B", "br", "Br", "bR", "BR", "rb", "rB", "Rb", "RB",
               "f", "F", "fr", "Fr", "fR", "FR", "rf", "rF", "Rf", "RF",
               "t", "T", "tr", "Tr", "tR", "TR", "rt", "rT", "Rt", "RT"]:
    assert_compiles(prefix + "'x'")
for prefix in ["ub", "ur", "bu", "ru", "fb", "bf", "uf", "tb", "bt", "ft", "tf", "ut", "rr", "bb"]:
    assert_syntax_error(prefix + "'x'")

# Escape sequences.
assert_eq("\\", chr(92))
assert_eq("\'\"", "'" + '"')
assert_eq("\a\b\f\n\r\t\v", "".join(map(chr, [7, 8, 12, 10, 13, 9, 11])))
assert_eq("\0", chr(0))
assert_eq("\101\1012", "AA2")
assert_eq("\x41\x7e", "A~")
assert_eq("\u00e9\U0001F600", "é" + chr(0x1F600))
assert_eq("\N{LATIN SMALL LETTER E WITH ACUTE}", "é")
assert_eq("\N{EM DASH}", chr(0x2014))
assert_eq("a\
b", "ab")
assert_syntax_error(r"'\x4'")
assert_syntax_error(r"'\u12'")
assert_syntax_error(r"'\U0011ffff'")
assert_syntax_error(r"'\N{NOT A REAL NAME}'")
assert_syntax_error(r"'\N'")
# Octal escapes above \377 are allowed in str (with a warning), giving the code point.
assert_eq(eval(r"'\777'"), chr(0o777))
# Unrecognized escapes are left in the string (with a SyntaxWarning).
assert_eq(eval(r"'\d'"), "\\d")
assert_eq(len(eval(r"'\q'")), 2)

# Raw strings keep backslashes; a raw string cannot end in an odd backslash.
assert_eq(r"\n", "\\n")
assert_eq(r"\"", '\\"')
assert_eq(R'\x41', "\\x41")
assert_eq(len(r"\\"), 2)
assert_syntax_error(r"r'\'")
assert_eq(r"""a\
b""", "a\\\nb")

# Unterminated literals.
assert_syntax_error("'abc")
assert_syntax_error("'abc\ndef'")
assert_syntax_error('"""abc')

# Bytes literals are ASCII only and give bytes.
assert_eq(b"abc", bytes([97, 98, 99]))
assert_type(b"", bytes)
assert_eq(b"\x00\xff\n\101", bytes([0, 255, 10, 65]))
assert_eq(b"\u1234", b"\\u1234")  # \u is not an escape in bytes
assert_eq(b"\N{EM DASH}", b"\\N{EM DASH}")
assert_syntax_error("b'é'")
assert_eq(rb"\x00", b"\\x00")
assert_syntax_error("b'a' 'b'")
assert_syntax_error("'a' b'b'")
assert_eq(b"a" b'b' B"c", b"abc")

# A u prefix is accepted for compatibility and changes nothing.
assert_eq(u"abc", "abc")
assert_type(u"x", str)

# Literals and identity: equal immutable literals may share objects; type is fixed.
assert_type("x", str)
assert_type("""x""", str)
