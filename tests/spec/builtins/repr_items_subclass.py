# spec: PLS-315 7.5.6, 25.1.2, 25.2
# description: the repr of a list, tuple, dict or set, through repr(),
# str(), format() and an f-string field, calls the Python __repr__ of an
# item that is an instance of a builtin type's subclass defining it before
# the builtin type, and of a class item its metaclass's, each in order; a
# subclass without one shows its builtin repr, and a result that is no str
# is a TypeError; inside functions as at module level.
from harness import *

log = []

class S(str):
    def __repr__(self):
        for i in range(2): pass
        log.append("S")
        return "S!"
class I(int):
    def __repr__(self): log.append("I"); return "I!"
class N(int): pass
class M(type):
    def __repr__(cls): log.append(cls.__name__); return "M!" + cls.__name__
class C(metaclass=M): pass
class Bad(list):
    def __repr__(self): return 5

def reprs():
    out = [repr([S("b"), I(1), N(2), C]), str((C, {S("k"): I(3)})), f"{[C]}", repr({C, 1} - {1}), format([S("x")])]
    out.append(log[:]); del log[:]
    try: repr([Bad()])
    except TypeError as e: out.append(str(e))
    return out

expected = ["[S!, I!, 2, M!C]", "(M!C, {S!: I!})", "[M!C]", "{M!C}", "[S!]",
            ["S", "I", "C", "C", "S", "I", "C", "C", "S"], "Bad.__repr__() must return a str, not int"]
assert_eq(reprs(), expected)
del log[:]
assert_eq(repr([S("b"), C]), "[S!, M!C]")
assert_eq(log, ["S", "C"])
