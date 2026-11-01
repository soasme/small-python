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
