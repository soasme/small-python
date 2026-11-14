# spec: PLS-315 23.4, 7.5.5, 7.5.6, 19.3.5
# description: str.format and format_map with a conversion !r, !s or !a
# of an instance whose Python __repr__ or __str__, which may loop, makes
# the text, in field order, before the next field's object is converted;
# !a escapes the text, and a spec then formats it as a str, not through
# the instance's __format__; a non-str result is a TypeError and any
# other exception propagates, the fields after it unconverted; a class
# with only __repr__ serves !s too. Inside functions as at module level.
from harness import *

log = []

class R:
    def __init__(self, t): self.t = t
    def __repr__(self):
        for _ in (): pass
        log.append("r" + self.t)
        return "R\xe9" + self.t
    def __str__(self):
        for _ in (): pass
        log.append("s" + self.t)
        return "s" + self.t
    def __format__(self, spec):
        for _ in (): pass
        log.append("f" + self.t)
        return "F" + spec

class OnlyRepr:
    def __repr__(self):
        for _ in (): pass
        log.append("o")
        return "o"

class Bad:
    def __repr__(self):
        for _ in (): pass
        return 3

class Raise:
    def __str__(self):
        for _ in (): pass
        raise LookupError("x")

def formats():
    return ["{!r}|{!s}|{!a}|{}".format(R("1"), R("2"), R("3"), R("4")),
            "{0!r:>8}|{x!s:*^5}|{1!a:.3}".format(R("a"), R("b"), x=R("c")),
            "{!s} {!r}".format(OnlyRepr(), OnlyRepr()),
            "{0!r}{0!s}".format(R("z")), str.format("{!r}", R("m")),
            "{k!a:>6}".format_map({"k": R("k")})]

expected = ["R\xe91|s2|R\\xe93|F", "     R\xe9a|*sc**|R\\x", "o o", "R\xe9zsz", "R\xe9m", "R\\xe9k"]
expected_log = ["r1", "s2", "r3", "f4", "ra", "sc", "rb", "o", "o", "rz", "sz", "rm", "rk"]
assert_eq(formats(), expected)
assert_eq(log, expected_log)
log.clear()

assert_eq("{!r}|{!s}|{!a}|{}".format(R("1"), R("2"), R("3"), R("4")), expected[0])
assert_eq(log, expected_log[:4])
log.clear()

def errors():
    out = []
    try: "{!r}".format(Bad())
    except TypeError as e: out.append(str(e))
    try: "{!s}{!r}".format(Raise(), R("after"))
    except LookupError as e: out.append(e.args)
    return out

assert_eq(errors(), ["Bad.__repr__() must return a str, not int", ("x",)])
assert_eq(log, [])
