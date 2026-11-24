# spec: PLS-315 16.4.3, 23.3.1, 5.2.6, 13.3.4, 13.2.3, 7.9.1, 26.1
# description: type.__new__'s namespace, str()'s encoding and errors, a
# ** unpacking of a non-mapping in a call or a display, an unhashable
# dict key or set element, and a with or async with statement's object
# that is no context manager, name its class by fully qualified name;
# bytes(), bytearray(), decode() and encode(), a * unpacking and the
# unhashable type itself are named by the class's name.
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
def unhashable():
    class Keyed:
        __hash__ = None
    return Keyed()
def containers():
    out = []
    for f in (lambda: {unhashable(): 1}, lambda: {unhashable()}, lambda: frozendict([(unhashable(), 1)]), lambda: set([unhashable()])):
        try: f()
        except TypeError as e: out.append(str(e))
    return out
assert_eq(containers(), ["cannot use 'unhashable.<locals>.Keyed' as a dict key (unhashable type: 'Keyed')",
                         "cannot use 'unhashable.<locals>.Keyed' as a set element (unhashable type: 'Keyed')",
                         "cannot use 'unhashable.<locals>.Keyed' as a frozendict key (unhashable type: 'Keyed')",
                         "cannot use 'unhashable.<locals>.Keyed' as a set element (unhashable type: 'Keyed')"])
def managers():
    out = []
    try:
        with x: pass
    except TypeError as e: out.append(str(e))
    async def entered():
        async with x: pass
    try: entered().send(None)
    except TypeError as e: out.append(str(e))
    return out
assert_eq(managers(), ["'make.<locals>.Local' object does not support the context manager protocol (missed __exit__ method)",
                       "'make.<locals>.Local' object does not support the asynchronous context manager protocol (missed __aexit__ method)"])
