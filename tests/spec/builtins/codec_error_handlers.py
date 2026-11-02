# spec: PLS-315 23.3.1
# description: The surrogateescape, surrogatepass and backslashreplace error handlers, and the type of the errors argument.
from harness import *

# surrogateescape: lone surrogates U+DC80..U+DCFF stand for the bytes they escape.
assert_eq("a\udc80b".encode("utf-8", "surrogateescape"), b"a\x80b")
assert_eq("\xe9\udc80".encode("latin-1", "surrogateescape"), b"\xe9\x80")
assert_eq(b"a\x80b".decode("utf-8", "surrogateescape"), "a\udc80b")
assert_eq(b"a\x80b".decode("utf-8", "surrogateescape").encode("utf-8", "surrogateescape"), b"a\x80b")
# surrogatepass: UTF-8 three-byte surrogate sequences pass both ways.
assert_eq(b"\xe2\x82\xac\xed\xa0\x80".decode("utf-8", "surrogatepass"), "€\ud800")
assert_eq("\ud800".encode("utf-8", "surrogatepass"), b"\xed\xa0\x80")
# backslashreplace on decoding writes each undecodable byte as \xhh.
assert_eq(b"a\x80\xffb".decode("utf-8", "backslashreplace"), "a\\x80\\xffb")
assert_eq(str(assert_raises(TypeError, "a".encode, "utf-8", 1)), "encode() argument 'errors' must be str, not int")
# namereplace writes a character's Unicode name, never an alias; a character
# without a name (a control, a private use character) takes backslashreplace.
assert_eq("a€\xe9".encode("ascii", "namereplace"), b"a\\N{EURO SIGN}\\N{LATIN SMALL LETTER E WITH ACUTE}")
assert_eq("Ƣ".encode("ascii", "namereplace"), b"\\N{LATIN CAPITAL LETTER OI}")
assert_eq("각一\U0001f600".encode("latin-1", "namereplace"), b"\\N{HANGUL SYLLABLE GAG}\\N{CJK UNIFIED IDEOGRAPH-4E00}\\N{GRINNING FACE}")
assert_eq("\x85\U0010ffff".encode("ascii", "namereplace"), b"\\x85\\ue000\\U0010ffff")
assert_raises(TypeError, b"\xff".decode, "utf-8", "namereplace", message="don't know how to handle UnicodeDecodeError in error callback")
