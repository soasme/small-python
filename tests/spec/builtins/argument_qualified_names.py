# spec: PLS-315 16.4.3, 23.3.1, 5.2.6
# description: type.__new__'s namespace and str()'s encoding and errors
# that are of the wrong type name its class by fully qualified name;
# bytes(), bytearray(), decode() and encode() name it by its name.
from harness import *
def make():
    class Local: pass
    return Local()
x = make()
def messages():
    out = []
    for f in (lambda: type("N", (), x), lambda: type(x, (), {}), lambda: str(b"", x), lambda: str(b"", "utf-8", x),
              lambda: b"".decode(x), lambda: "".encode("utf-8", x), lambda: bytes("", x), lambda: bytearray("", "utf-8", x)):
        try: f()
        except TypeError as e: out.append(str(e))
    return out
assert_eq(messages(), ["type.__new__() argument 3 must be dict or frozendict, not make.<locals>.Local",
                       "type.__new__() argument 1 must be str, not Local",
                       "str() argument 'encoding' must be str, not make.<locals>.Local",
                       "str() argument 'errors' must be str, not make.<locals>.Local",
                       "decode() argument 'encoding' must be str, not Local", "encode() argument 'errors' must be str, not Local",
                       "bytes() argument 'encoding' must be str, not Local", "bytearray() argument 'errors' must be str, not Local"])
