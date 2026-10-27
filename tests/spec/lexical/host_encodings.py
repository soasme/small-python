# spec: PLS-315 B.2, 11.2, 23.3.1
# description: Encodings outside the core three come from the host, which may know them or not.
from harness import *

# An encoding the host does not know is an error in source and in codecs.
e = assert_raises(SyntaxError, compile, b"# coding: spec-no-such-codec\nx = 1\n", "<spec>", "exec")
assert_eq(e.msg, "unknown encoding: spec-no-such-codec")
e = assert_raises(LookupError, "x".encode, "spec-no-such-codec")
assert_eq(str(e), "unknown encoding: spec-no-such-codec")
e = assert_raises(LookupError, b"x".decode, "spec-no-such-codec")
assert_eq(str(e), "unknown encoding: spec-no-such-codec")

# cp1252 is not a core encoding: HostDecodeSource and HostLookupCodec decide.
# A host that knows it decodes 0x80 as the euro sign in source and codecs alike.
source = b"# coding: cp1252\ns = '\x80'\n"
try:
    code = compile(source, "<spec>", "exec")
except SyntaxError as e:
    assert_eq(e.msg, "unknown encoding: cp1252")
    assert_raises(LookupError, "€".encode, "cp1252")
else:
    ns = {}
    exec(code, ns)
    assert_eq(ns["s"], "€")
    assert_eq("€".encode("cp1252"), b"\x80")
    assert_eq(b"\x80".decode("cp1252"), "€")
    # The host's codec reports errors with the core exception types.
    assert_raises(UnicodeEncodeError, "Ā".encode, "cp1252")
    assert_eq("Ā".encode("cp1252", "replace"), b"?")
