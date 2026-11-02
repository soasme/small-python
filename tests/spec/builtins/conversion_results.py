# spec: PLS-315 7.5.5, 7.5.6, 7.5.8, 19.3.5, 19.3.16, 19.3.32, 23.5.7, 23.6
# description: str(), repr(), ascii() and format() return what the special method returned, a str subclass included.
from harness import *

class S(str):
    pass

class Repr:
    def __repr__(self):
        return S("<r>")

class Str:
    def __str__(self):
        return S("s")

class Format:
    def __format__(self, spec):
        return S("f" + spec)

class Meta(type):
    def __repr__(cls):
        return S("meta")

class Classy(metaclass=Meta):
    pass

def typed(value, expected, kind):
    assert_eq(value, expected)
    assert_is(type(value), kind)

# ToStr and ToRepr return the method's result itself.
typed(repr(Repr()), "<r>", S)
typed(str(Repr()), "<r>", S)
typed(str(Str()), "s", S)
typed(repr(Classy), "meta", S)
typed(ascii(Repr()), "<r>", S)
plain = "text"
class Same:
    def __str__(self):
        return plain
assert_is(str(Same()), plain)
# str() of a str subclass without its own __str__ is an exact str.
typed(str(S("q")), "q", str)

# Format returns the __format__ result; object.__format__ returns ToStr's.
typed(format(Format()), "f", S)
typed(format(Format(), "x"), "fx", S)
typed(format(Str()), "s", S)
typed(object.__format__(Str(), ""), "s", S)

# Built into larger text, the results are read as strs.
typed(f"{Format():y}!", "fy!", str)
typed("{}!".format(Format()), "f!", str)
typed(f"<{Str()}>", "<s>", str)
typed("%s|%r|%a" % (Str(), Repr(), Repr()), "s|<r>|<r>", str)
typed(b"%r|%a" % (Repr(), Repr()), b"<r>|<r>", bytes)

class NotText:
    def __format__(self, spec):
        return 1
assert_eq(str(assert_raises(TypeError, format, NotText())), "NotText.__format__() must return a str, not int")

# str.maketrans takes an exact dict or frozendict.
assert_eq(str.maketrans(frozendict({"a": "b"})), {97: "b"})
class D(dict):
    pass
assert_eq(str(assert_raises(TypeError, str.maketrans, D(a="b"))), "if you give only one argument to maketrans it must be a dict")
