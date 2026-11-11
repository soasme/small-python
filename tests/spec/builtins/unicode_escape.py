# spec: PLS-315 23.3.1, 23.3.2
# description: The unicode_escape codec: escape sequences on decoding, escaped characters on encoding, and its errors.
from harness import *

# Each byte that starts no escape stands for the code point of its value.
assert_eq(b"\xc3\xa9".decode("unicode_escape"), "\xc3\xa9")
assert_eq(b"a\x80\xff".decode("unicode_escape"), "a\x80\xff")
assert_eq(str(b"\\n", "unicode_escape"), "\n")
assert_eq(bytearray(b"\\x41").decode("unicode-escape"), "A")
assert_eq(b"x".decode("UNICODE ESCAPE"), "x")
# The escape sequences of string literals.
assert_eq(b"a\\\nb".decode("unicode_escape"), "ab")
assert_eq(b"\\\\\\'\\\"\\a\\b\\f\\n\\r\\t\\v".decode("unicode_escape"), "\\'\"\a\b\f\n\r\t\v")
assert_eq(b"\\0\\12\\1011\\777".decode("unicode_escape"), "\x00\nA1\u01ff")
assert_eq(b"\\x41\\u00e9\\U0001F600".decode("unicode_escape"), "A\xe9\U0001f600")
assert_eq(b"\\N{BULLET}\\N{latin small letter a}\\N{BEL}".decode("unicode_escape"), "\u2022a\x07")
# An unknown escape keeps its backslash.
assert_eq(b"\\q\\8\\\xff".decode("unicode_escape"), "\\q\\8\\\xff")


def fails(data, start, end, reason):
    e = assert_raises(UnicodeDecodeError, data.decode, "unicode_escape")
    assert_eq((e.encoding, e.object, e.start, e.end, e.reason), ("unicodeescape", data, start, end, reason))


fails(b"\\", 0, 1, "\\ at end of string")
fails(b"ab\\x4", 2, 5, "truncated \\xXX escape")
fails(b"\\x4g", 0, 3, "truncated \\xXX escape")
fails(b"\\u12", 0, 4, "truncated \\uXXXX escape")
fails(b"\\U0001", 0, 6, "truncated \\UXXXXXXXX escape")
fails(b"\\U00110000", 0, 10, "illegal Unicode character")
fails(b"\\N", 0, 2, "malformed \\N character escape")
fails(b"\\Nab", 0, 2, "malformed \\N character escape")
fails(b"\\N{abc", 0, 6, "malformed \\N character escape")
fails(b"\\N{}x", 0, 3, "malformed \\N character escape")
fails(b"\\N{xx}", 0, 6, "unknown Unicode character name")
assert_eq(str(assert_raises(UnicodeDecodeError, b"\\".decode, "unicode_escape")),
          "'unicodeescape' codec can't decode byte 0x5c in position 0: \\ at end of string")
assert_eq(str(assert_raises(UnicodeDecodeError, b"\\x".decode, "unicode_escape")),
          "'unicodeescape' codec can't decode bytes in position 0-1: truncated \\xXX escape")

# Error handlers see the faulty escape; surrogateescape cannot stand for its ASCII bytes.
assert_eq(b"\\x4g\\x41".decode("unicode_escape", "ignore"), "gA")
assert_eq(b"\\x4g".decode("unicode_escape", "replace"), "\ufffdg")
assert_eq(b"\\N{".decode("unicode_escape", "backslashreplace"), "\\x5c\\x4e\\x7b")
assert_raises(UnicodeDecodeError, b"\\x".decode, "unicode_escape", "surrogateescape")
assert_raises(UnicodeDecodeError, b"\\x".decode, "unicode_escape", "surrogatepass")
assert_raises(TypeError, b"\\x".decode, "unicode_escape", "xmlcharrefreplace",
              message="don't know how to handle UnicodeDecodeError in error callback")
assert_raises(LookupError, b"\\x".decode, "unicode_escape", "bogus", message="unknown error handler name 'bogus'")
assert_eq(b"a".decode("unicode_escape", "bogus"), "a")

# Encoding never fails: printable ASCII is kept, other characters are escaped.
assert_eq("a\t\n\r\\'\"".encode("unicode_escape"), b"a\\t\\n\\r\\\\'\"")
assert_eq("\x00\x7f\x80\xe9\uffff\U0001f600\ud800".encode("unicode_escape"),
          b"\\x00\\x7f\\x80\\xe9\\uffff\\U0001f600\\ud800")
assert_eq("\xe9".encode("unicode_escape", "bogus"), b"\\xe9")
assert_raises(LookupError, "a".encode, "unicodeescape", message="unknown encoding: unicodeescape")

