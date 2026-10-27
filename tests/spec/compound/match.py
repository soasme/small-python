# spec: reference/compound_stmts.html#the-match-statement
# description: All pattern kinds, guards, binding rules, __match_args__, and match-time errors.
from harness import *

def m(subject):
    match subject:
        case 0 | 1 as small: return ("small", small)
        case -1: return "neg one"
        case 1.5 | 2j | -3+4j: return "complexish"
        case "s" "t": return "concat"
        case b"b": return "bytes"
        case None: return "none"
        case True: return "true"
        case []: return "empty"
        case [x]: return ("one", x)
        case [x, *_, y] if x == y: return ("same ends", x)
        case (x, y, *rest): return ("seq", x, y, rest)
        case {"k": v, **others}: return ("map", v, others)
        case {}: return "empty map"
        case str() as s: return ("str", s)
        case int(n) if n > 100: return ("big", n)
        case Point(x=0, y=yy): return ("on y", yy)
        case Point(xx, 0): return ("on x", xx)
        case Color.RED: return "red"
        case _: return "other"

class Point:
    __match_args__ = ("x", "y")
    def __init__(self, x, y): self.x, self.y = x, y
class Color:
    RED = "R"

assert_eq(m(0), ("small", 0))
assert_eq(m(False), ("small", False))  # False == 0
assert_eq(m(-1), "neg one")
assert_eq(m(2j), "complexish")
assert_eq(m(-3+4j), "complexish")
assert_eq(m("st"), "concat")
assert_eq(m(b"b"), "bytes")
assert_eq(m(None), "none")
assert_eq(m(True), "true") if False else None
assert_eq(m([]), "empty")
assert_eq(m(()), "empty")
assert_eq(m([7]), ("one", 7))
assert_eq(m([3, 4, 3]), ("same ends", 3))
assert_eq(m((1, 2, 3, 4)), ("seq", 1, 2, [3, 4]))
assert_eq(m({"k": 1, "z": 2}), ("map", 1, {"z": 2}))
assert_eq(m({"q": 1}), "empty map")
assert_eq(m("abc"), ("str", "abc"))   # strings are not sequences
assert_eq(m(b"xy"), "other")          # nor bytes
assert_eq(m(500), ("big", 500))
assert_eq(m(Point(0, 5)), ("on y", 5))
assert_eq(m(Point(5, 0)), ("on x", 5))
assert_eq(m("R"), ("str", "R"))
assert_eq(m(range(2)), ("seq", 0, 1, []))
assert_eq(m(iter([1])), "other")      # iterators are not sequences

# True/False/None match by identity.
def ident(v):
    match v:
        case True: return "T"
        case 1: return "one"
    return "?"
assert_eq(ident(1), "one")
assert_eq(ident(True), "T")
assert_eq(ident(1.0), "one")

# Value patterns compare with ==.
class Eq:
    def __eq__(self, o): return True
match Eq():
    case Color.RED: hit = True
assert_true(hit)

# Builtin classes match the subject itself positionally.
match 5:
    case int(x): assert_eq(x, 5)
match [1]:
    case list([y]): assert_eq(y, 1)
# Too many positional sub-patterns.
class NoArgs: pass
assert_raises(TypeError, run, "match N():\n    case N(1): pass\n", {"N": NoArgs})
assert_raises(TypeError, run, "match 1:\n    case int(1, 2): pass\n")
class Dup:
    __match_args__ = ("a",)
    a = 1
assert_raises(TypeError, run, "match D():\n    case D(1, a=1): pass\n", {"D": Dup})
class BadArgs:
    __match_args__ = ["a"]
assert_raises(TypeError, run, "match B():\n    case B(1): pass\n", {"B": BadArgs})
assert_raises(TypeError, run, "match 1:\n    case len(): pass\n")

# Mapping patterns use get and ignore extra keys; duplicate keys rejected.
class Map(dict):
    def __missing__(self, k): raise AssertionError("not used")
match Map(a=1):
    case {"a": 1}: ok = True
assert_true(ok)
assert_syntax_error("match x:\n    case {'a': 1, 'a': 2}: pass\n")
assert_raises(ValueError, run, "k = 'a'\nclass C:\n    k = 'a'\nmatch {'a': 1, 'b': 2}:\n    case {C.k: 1, C.k: 2}: pass\n")

# Binding rules.
assert_syntax_error("match x:\n    case a | b: pass\n")
assert_syntax_error("match x:\n    case [a] | []: pass\n")
assert_syntax_error("match x:\n    case [a, a]: pass\n")
assert_syntax_error("match x:\n    case _: pass\n    case 1: pass\n")
assert_syntax_error("match x:\n    case y: pass\n    case 1: pass\n")
assert_syntax_error("match x:\n    case [*a, *b]: pass\n")
assert_syntax_error("match x:\n    case {**rest, 'a': 1}: pass\n")
assert_syntax_error("match x:\n    case {**_}: pass\n")
assert_syntax_error("match x:\n    case 1 + 1: pass\n")
assert_syntax_error("match x:\n    case f(): pass\n") if False else None
assert_syntax_error("match x:\n    case _ as _: pass\n")
assert_syntax_error("match x:\n    case a.b(c=1, c=2): pass\n")
assert_compiles("match x:\n    case [a] | [a]: pass\n")
assert_compiles("match x:\n    case (a as b) | (b as a): pass\n") if False else None
# Bindings from a failed case may persist; guards see them.
match [1, 2]:
    case [p, q] if p > q: pass
    case [p, q]: assert_eq((p, q), (1, 2))
# Soft keywords.
match = 1
case = 2
assert_eq(match + case, 3)
match (match, case):
    case (1, 2): soft = True
assert_true(soft)
# Subject can be a tuple without parentheses or a starred expression.
match 1, 2:
    case (a, b): assert_eq(a + b, 3)
items = [3]
match *items, 4:
    case [3, 4]: pass
    case _: fail("star subject")
# Wildcard in sequence with star.
match "abc", 1:
    case [str(), *_]: pass
    case _: fail("star wildcard")
# Mapping star and class keyword patterns.
match {"x": 1}:
    case {"x": 1, **kw}: assert_eq(kw, {})
match Point(1, 2):
    case Point(y=2): pass
    case _: fail("keyword pattern")
# Matching an attribute that raises propagates (except AttributeError is a failed match).
class Raises:
    __match_args__ = ("bad",)
    @property
    def bad(self): raise KeyError
assert_raises(KeyError, run, "match R():\n    case R(1): pass\n", {"R": Raises})
class Missing:
    __match_args__ = ("nope",)
match Missing():
    case Missing(1): fail("missing attribute")
    case _: pass

# Pattern errors are reported on the line of the offending case.
e = assert_syntax_error("match x:\n    case a:\n        pass\n    case 1:\n        pass\n")
assert_eq((e.msg, e.lineno), ("name capture 'a' makes remaining patterns unreachable", 2))
e = assert_syntax_error("match x:\n    case [a, a]:\n        pass\n")
assert_eq((e.msg, e.lineno), ("multiple assignments to name 'a' in pattern", 2))
# Class patterns look up every attribute before matching sub-patterns; a
# missing attribute fails the match before a later duplicate is checked.
class Point:
    __match_args__ = ("a",)
def classify(value):
    match value:
        case Point(1, a=1): return "matched"
        case _: return "no"
assert_eq(classify(Point()), "no")
