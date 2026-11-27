# spec: PLS-315 15.6.1, 8.3.1
# description: a case pattern's early errors are found after every error of
# Clause 8, in source order with the other errors found after them, a case's
# pattern before its guard and block; within a pattern in the order it is
# visited, each at the pattern it names.
from harness import *

def error(body, before="", after=""):
    caught = assert_syntax_error(before + "match v:\n    " + body + "\n" + after)
    return caught.msg, caught.lineno, caught.offset, caught.end_offset

SCOPE = "def f():\n    q = 1\n    global q\n"
GLOBAL = "name 'q' is assigned to before global declaration"
# Clause 8 errors come first, before or after the match.
for body in ["case [a, a]: pass", "case {1: a, 1: b}: pass", "case [*a, *b]: pass", "case f'x': pass",
             "case C(a=1, a=2): pass", "case x: pass\n    case 1: pass"]:
    assert_eq(error(body, before=SCOPE)[0], GLOBAL)
    assert_eq(error(body, after=SCOPE)[0], GLOBAL)
# A parse error comes before them all.
assert_eq(assert_syntax_error("match v:\n    case [a, a]: pass\nx = (\n").msg, "'(' was never closed")
# A case's pattern before its guard and block; an earlier case's block first.
assert_eq(error("case [a, a] if (yield): pass"), ("multiple assignments to name 'a' in pattern", 2, 14, 15))
assert_eq(error("case x:\n        return 1\n    case 1: pass"), ("name capture 'x' makes remaining patterns unreachable", 2, 10, 11))
assert_eq(error("case 1:\n        return 1\n    case x: pass\n    case 2: pass"), ("'return' outside function", 3, 9, 17))
assert_eq(error("case [a, a]: pass\n    case {1: b, 1: c}: pass"), ("multiple assignments to name 'a' in pattern", 2, 14, 15))
assert_eq(error("case {1: b, 1: c}: pass\n    case [a, a]: pass"), ("mapping pattern checks duplicate key (1)", 2, 10, 22))
# Within a pattern, in visiting order.
assert_eq(error("case [a, {1: b, 1: c}, a]: pass"), ("mapping pattern checks duplicate key (1)", 2, 14, 26))
assert_eq(error("case {1: a, 1: a}: pass"), ("mapping pattern checks duplicate key (1)", 2, 10, 22))
assert_eq(error("case {1: a, f'x': b, 1: c}: pass"), ("mapping pattern keys may only match literals and attribute lookups", 2, 10, 31))
assert_eq(error("case {1: a, 1: b, f'x': c}: pass"), ("mapping pattern checks duplicate key (1)", 2, 10, 31))
assert_eq(error("case {1: a, True: b}: pass"), ("mapping pattern checks duplicate key (True)", 2, 10, 25))
assert_eq(error("case {1: a, 1: b} | {2: c}: pass"), ("mapping pattern checks duplicate key (1)", 2, 10, 22))
assert_eq(error("case [*a, *b, a]: pass"), ("multiple starred names in sequence pattern", 2, 10, 21))
assert_eq(error("case *a, *b: pass"), ("multiple starred names in sequence pattern", 2, 10, 16))
assert_eq(error("case C(a=1, b=2, b=3, a=4): pass"), ("attribute name repeated in class pattern: a", 2, 29, 30))
assert_eq(error("case [1, f'x', a, a]: pass"), ("patterns may only match literals and attribute lookups", 2, 14, 18))
# Each alternative of an or-pattern binds names of its own; only the last may be irrefutable.
assert_eq(error("case [a, (a | b)]: pass"), ("name capture 'a' makes remaining patterns unreachable", 2, 15, 16))
assert_eq(error("case (a | [a]): pass"), ("name capture 'a' makes remaining patterns unreachable", 2, 11, 12))
assert_eq(error("case [a, ([a] | [b])]: pass"), ("alternative patterns bind different names", 2, 15, 24))
assert_eq(error("case [a, ([a] | [a])]: pass"), ("multiple assignments to name 'a' in pattern", 2, 15, 24))
assert_eq(error("case [a, a] | x: pass"), ("multiple assignments to name 'a' in pattern", 2, 14, 15))
# __debug__ is an error of Clause 8, so it comes before them, a class
# pattern's keyword after its positional sub-patterns.
assert_eq(error("case [a, a, __debug__]: pass"), ("cannot assign to __debug__", 2, 17, 26))
assert_eq(error("case C(a=1, __debug__=2, a=3): pass"), ("cannot assign to __debug__", 2, 27, 28))
assert_eq(error("case C(x=__debug__, __debug__=1): pass"), ("cannot assign to __debug__", 2, 35, 36))
assert_eq(error("case C(__debug__, __debug__=1): pass"), ("cannot assign to __debug__", 2, 12, 21))
# A mapping key is a literal or a dotted name.
for body, offset in [("case {x: a}: pass", 12), ("case {C(): a}: pass", 12), ("case {(1): a}: pass", 11), ("case {[1]: a}: pass", 11)]:
    assert_eq(error(body), ("invalid syntax", 2, offset, offset + 1))
# A pattern may capture any number of names.
names = ", ".join("a%d" % i for i in range(300))
space = {"v": list(range(300))}
exec("match v:\n    case [" + names + "]: r = a299\n", space)
assert_eq(space["r"], 299)
