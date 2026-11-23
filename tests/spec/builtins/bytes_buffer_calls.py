# spec: PLS-315 24.4.1, 24.4.2
# description: bytes() of an instance without __bytes__ and bytearray()
# of an instance, neither with a bytes or bytearray base, call its class's
# Python __buffer__, which may loop, with the flags, copy the view it
# returns and then call its Python __release_buffer__ with that view: a
# __buffer__ result not a memoryview raises TypeError and an exception of
# __buffer__ propagates, neither calling __release_buffer__. bytes()
# prefers __bytes__. Called directly, through map() and by a bytes
# format's %b, inside functions as at module level.
from harness import *

log = []

class Exporting:
    def __init__(self, data): self.data = bytearray(data)
    def __buffer__(self, flags):
        for _ in range(2): pass
        log.append(("buffer", flags))
        if self.data == b"bad": raise KeyError("buffer")
        if self.data == b"str": return "text"
        return memoryview(self.data)[1:]
    def __release_buffer__(self, view):
        for _ in range(2): pass
        log.append(("release", bytes(view)))

class Plain:
    def __buffer__(self, flags):
        log.append(("plain", flags))
        return memoryview(b"plain")

class Both(Exporting):
    def __bytes__(self): log.append("bytes"); return b"B"

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def copies():
    del log[:]
    out = [bytes(Exporting(b"xab")), bytearray(Exporting(b"xcd")), bytes(Plain()), bytearray(Plain()), bytes(Both(b"x")),
           bytearray(Both(b"xef")), list(map(bytes, [Exporting(b"xg"), Plain()])), list(map(bytearray, [Exporting(b"xh")]))]
    out.append(b"%b|" % (Exporting(b"xij"),))
    out += [error(lambda: bytes(Exporting(b"bad"))), error(lambda: bytearray(Exporting(b"str"))), list(log)]
    return out

expected = [b"ab", bytearray(b"cd"), b"plain", bytearray(b"plain"), b"B", bytearray(b"ef"), [b"g", b"plain"], [bytearray(b"h")], b"ij|",
            ("KeyError", "'buffer'"), ("TypeError", "Exporting.__buffer__() must return a memoryview, not str"),
            [("buffer", 284), ("release", b"ab"), ("buffer", 284), ("release", b"cd"), ("plain", 284), ("plain", 284), "bytes",
             ("buffer", 284), ("release", b"ef"), ("buffer", 284), ("release", b"g"), ("plain", 284), ("buffer", 284), ("release", b"h"),
             ("buffer", 284), ("release", b"ij"), ("buffer", 284), ("buffer", 284)]]

def main():
    return copies()

assert_eq(main(), expected)
assert_eq(copies(), expected)

# A %b of an exporter without __release_buffer__ copies its view.
del log[:]
assert_eq((b"<%b>" % (Plain(),), b"%s|%b" % (Plain(), Plain()), log), (b"<plain>", b"plain|plain", [("plain", 284)] * 3))

# A native __bytes__ converts a %b's and %s's value; one giving no bytes is
# a TypeError.
class NativeBytes:
    __bytes__ = b"ok".__bytes__
class NativeText:
    __bytes__ = "x".__str__
assert_eq(b"%b|%s" % (NativeBytes(), NativeBytes()), b"ok|ok")
with assert_raises(TypeError, message="NativeText.__bytes__() must return a bytes, not str"):
    b"%b" % NativeText()
