# spec: PLS-315 7.6.2
# description: a built-in sequence's __add__ is its concatenation and
# raises the sequence clause's TypeError for an operand it cannot
# concatenate, where a number's method returns NotImplemented; so an
# exact sequence still reaches the other operand's __radd__, while a
# subclass defining __radd__, whose inherited __add__ then answers first,
# raises. Inside functions as at module level.
from harness import *

class R:
    def __radd__(self, o):
        for _ in (): pass
        return "R"

class S(str): pass

class B(str):
    def __radd__(self, o):
        for _ in (): pass
        return "B"

class L(list):
    def __radd__(self, o): return "L"

def concatenations():
    out = [str.__add__("a", S("b")), list.__add__([1], [2]), bytes.__add__(b"a", bytearray(b"b")), int.__add__(1, "a")]
    for call in (lambda: str.__add__("a", R()), lambda: str.__add__("a", 1), lambda: list.__add__([1], (2,)),
                 lambda: tuple.__add__((1,), R()), lambda: bytes.__add__(b"a", R()), lambda: B("a") + R(),
                 lambda: L([1]) + R(), lambda: B("a") + 1):
        out.append(str(assert_raises(TypeError, call)))
    return out + ["a" + R(), [1] + R(), (1,) + R(), S("a") + R(), R() + B("a"), B("a") + "b"]

expected = ["ab", [1, 2], b"ab", NotImplemented,
            'can only concatenate str (not "R") to str', 'can only concatenate str (not "int") to str',
            'can only concatenate list (not "tuple") to list', 'can only concatenate tuple (not "R") to tuple',
            "can't concat R to bytes", 'can only concatenate str (not "R") to str',
            'can only concatenate list (not "R") to list', 'can only concatenate str (not "int") to str',
            "R", "R", "R", "R", "B", "ab"]

def main():
    return concatenations()

assert_eq(main(), expected)
assert_eq(concatenations(), expected)
