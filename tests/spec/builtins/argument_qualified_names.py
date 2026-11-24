# spec: PLS-315 16.4.3, 23.3.1, 5.2.6, 13.3.4, 13.2.3
# description: type.__new__'s namespace, str()'s encoding and errors, and
# a ** unpacking of a non-mapping in a call or a display, of the wrong
# type, name its class by fully qualified name; bytes(), bytearray(),
# decode() and encode(), and a * unpacking, name it by its name.
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
def keywords(**k): pass
def unpackings():
    out = []
    for f in (lambda: keywords(**x), lambda: {**x}, lambda: dict(**x), lambda: keywords(*x)):
        try: f()
        except TypeError as e: out.append(str(e))
    return out
assert_eq(unpackings(), ["Value after ** must be a mapping, not make.<locals>.Local", "'make.<locals>.Local' object is not a mapping",
                         "Value after ** must be a mapping, not make.<locals>.Local", "Value after * must be an iterable, not Local"])
