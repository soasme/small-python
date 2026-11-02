# spec: PLS-315 23.1, 23.1.1, 24.3
# description: str() of exact strings and subclasses.
from harness import *

x = "An interesting piece of text"
assert x is str(x)


class Stringy(str):
    def __new__(cls, value=""):
        return str.__new__(cls, value)

    def __init__(self, value):
        self.x = "substr"


y = Stringy(1)
assert type(y) is Stringy, "Type of Stringy should be stringy"
assert type(str(y)) is str, "Str of a str-subtype should be a str."

assert y + " other" == "1 other"
assert y.x == "substr"

## Base strings currently get an attribute dict, but shouldn't.
# with assert_raises(AttributeError):
#     "hello".x = 5

# str() without an object is empty, after checking any codec arguments' types.
assert_eq(str(encoding="ascii"), "")
assert_eq(str(errors="no such handler", encoding="no such codec"), "")
assert_raises(TypeError, lambda: str(encoding=1), message="str() argument 'encoding' must be str, not int")
class Plain(str):
    pass
assert_eq(Plain(encoding="ascii"), "")
assert_is(type(Plain(errors="strict")), Plain)

# partition and rpartition give an immutable text without the separator back as itself.
assert_is(y.partition("x")[0], y)
assert_is(y.rpartition("x")[2], y)
assert_is(type(y.partition("1")[0]), str)
z = b"bytes"
assert_is(z.partition(b"x")[0], z)
w = bytearray(b"mutable")
assert_eq(w.partition(b"x")[0], w)
assert_is(w.partition(b"x")[0] is w, False)
