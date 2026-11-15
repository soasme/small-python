# spec: PLS-315 7.5.5, 7.5.8, 19.3.16, 23.6
# description: str() of an instance of a subclass of int, float, complex,
# list, tuple, dict, set or frozenset, whose base defines no __str__ of
# its own, calls the Python __repr__ its class defines, through str(),
# an f-string field and %s alike; format() with an empty spec, of such an
# instance or of one whose class defines __str__, gives its str(), the
# base's __format__ applying to any other spec; a str or bytes subclass
# keeps its base's __str__. Inside functions as at module level.
from harness import *

log = []

def note(x):
    for _ in (): pass
    log.append(x)

class R(int):
    def __repr__(self): note("R"); return "R!"

class F(float):
    def __repr__(self): note("F"); return "F!"

class L(list):
    def __repr__(self): note("L"); return "L!"

class D(dict):
    def __repr__(self): note("D"); return "D!"

class S(int):
    def __str__(self): note("S"); return "S!"

class T(str):
    def __repr__(self): note("T"); return "T!"

def run():
    return [str(R(1)), f"{F(2.5)}", "%s" % L([1]), str(D()), format(R(3), ""), format(S(4), ""), f"{S(5)}",
            format(R(6), "d"), format(S(7), "03"), str(T("t")), repr(T("t")), "%r" % R(8)]

expected = ["R!", "F!", "L!", "D!", "R!", "S!", "S!", "6", "007", "t", "T!", "R!"]
assert_eq(run(), expected)
assert_eq(log, ["R", "F", "L", "D", "R", "S", "S", "T", "R"])
log.clear()
assert_eq((str(R(9)), format(S(1)), log), ("R!", "S!", ["R", "S"]))
