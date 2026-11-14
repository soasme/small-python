# spec: PLS-315 7.5.5, 7.5.6, 19.3.1, 19.3.16, 19.3.18, 19.3.24, 19.3.33
# description: str(), repr(), format(), len(), hash(), int(), float(),
# complex(), abs(), round() with and without ndigits, reversed() and
# bytes() of an instance of a builtin type's subclass call the Python
# method its class defines in place of the builtin's, and of a class call
# its metaclass's; str() of either, with only __repr__ defined, and an
# int subclass's format() with an empty spec show that; a result of the wrong type raises TypeError; inside
# functions as at module level.
from harness import *

log = []

def note(x):
    for i in range(2): pass
    log.append(x)

class I(int):
    def __repr__(self): note("repr"); return "I!"
    def __str__(self): note("str"); return "Is"
    def __format__(self, s): note(("fmt", s)); return "If"
    def __int__(self): note("int"); return 5
    def __float__(self): note("float"); return 2.5
    def __abs__(self): note("abs"); return 9
    def __hash__(self): note("hash"); return 3
    def __round__(self, n=None): note(("round", n)); return 4
    def __complex__(self): note("complex"); return 1j

class R(int):
    def __repr__(self): note("R.repr"); return "R!"

class L(list):
    def __len__(self): note("len"); return 7
    def __reversed__(self): note("rev"); return iter([1])

class S(str):
    def __str__(self): note("S.str"); return "SS"

class B(bytes):
    def __bytes__(self): note("bytes"); return b"bb"

def subclasses():
    del log[:]
    i, r = I(1), R(2)
    out = [repr(i), str(i), format(i, "x"), int(i), float(i), abs(i), hash(i), round(i), round(i, 2), complex(i),
           repr(r), str(r), format(r), int(r), len(L([1])), list(reversed(L([1]))), str(S("a")), repr(S("a")),
           bytes(B(b"a"))]
    return out, log[:]

expected = (["I!", "Is", "If", 5, 2.5, 9, 3, 4, 4, 1j, "R!", "R!", "R!", 2, 7, [1], "SS", "'a'", b"bb"],
            ["repr", "str", ("fmt", "x"), "int", "float", "abs", "hash", ("round", None), ("round", 2), "complex",
             "R.repr", "R.repr", "R.repr", "len", "rev", "S.str", "bytes"])
assert_eq(subclasses(), expected)

class M(type):
    def __repr__(cls): note("repr"); return "M:" + cls.__name__
    def __len__(cls): note("len"); return 3
    def __hash__(cls): note("hash"); return 11
    def __int__(cls): note("int"); return 4
    def __abs__(cls): note("abs"); return 5
    def __round__(cls, n=None): note(("round", n)); return 6
    def __reversed__(cls): note("rev"); return iter("ab")

class Spec(type):
    def __str__(cls): note("str"); return "S!"
    def __format__(cls, spec): note(("fmt", spec)); return "F" + spec

class C(metaclass=M): pass
class D(metaclass=Spec): pass

def classes():
    del log[:]
    out = [repr(C), str(C), len(C), hash(C), int(C), abs(C), round(C), round(C, 1), list(reversed(C)),
           str(D), format(D, "x"), format(D)]
    return out, log[:]

expected_classes = (["M:C", "M:C", 3, 11, 4, 5, 6, 6, ["a", "b"], "S!", "Fx", "F"],
                    ["repr", "repr", "len", "hash", "int", "abs", ("round", None), ("round", 1), "rev", "str",
                     ("fmt", "x"), ("fmt", "")])
assert_eq(classes(), expected_classes)

class Wrong(type):
    def __repr__(cls): return 5
    def __len__(cls): return "x"
class W(metaclass=Wrong): pass
class WI(int):
    def __int__(self): return "x"
    def __repr__(self): return 5

def errors():
    out = []
    for f, x in ((repr, W), (str, W), (len, W), (int, WI(1)), (repr, WI(1)), (str, WI(1))):
        try: f(x)
        except TypeError as e: out.append(str(e))
    return out

assert_eq(errors(), ["Wrong.__repr__() must return a str, not int", "Wrong.__str__() must return a str, not int",
                     "'str' object cannot be interpreted as an integer", "WI.__int__() must return an int, not str",
                     "WI.__repr__() must return a str, not int", "WI.__str__() must return a str, not int"])
assert_eq(subclasses(), expected)
del log[:]
assert_eq((repr(C), len(C), log), ("M:C", 3, ["repr", "len"]))
