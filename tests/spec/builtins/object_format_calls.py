# spec: PLS-315 23.5.7, 7.5.5
# description: object.__format__ of an empty spec returns ToStr of its
# argument, calling a Python __str__, which may loop, and returning a str
# subclass result as is; a __str__ returning a non-str raises TypeError, a
# non-empty spec raises TypeError before any call, and the instance's own
# __format__ is not consulted. Called directly or through a variable, inside
# functions and generators as at module level.
from harness import *

log = []

class S(str): pass

class Str:
    def __str__(self):
        for _ in range(2): pass
        log.append("str")
        return S("s")

class Bad:
    def __str__(self):
        for _ in range(2): pass
        return 1

class Own:
    def __format__(self, spec): return "own"
    def __str__(self):
        for _ in range(2): pass
        return "str"

v = object.__format__(Str(), "")
assert_eq((v, type(v)), ("s", S))
assert_eq(object.__format__(Own(), ""), "str")
assert_eq(log, ["str"])
log.clear()
assert_raises(TypeError, object.__format__, Str(), "x")
assert_eq(log, [])
try: object.__format__(Bad(), "")
except TypeError as e: assert_eq(str(e), "Bad.__str__() must return a str, not int")
else: raise AssertionError("no TypeError")

def calls():
    f = object.__format__
    return [f(Str(), ""), object.__format__(Own(), "")]

def gen(): yield object.__format__(Str(), "")

assert_eq(calls(), ["s", "str"])
assert_eq(list(gen()), ["s"])
assert_eq(log, ["str", "str"])
assert_eq((object.__format__(5, ""), object.__format__(Str, "")), ("5", repr(Str)))
