# spec: PLS-315 23.4, 7.5.5, 7.5.6
# description: str.format and format_map of a list, tuple, dict, set or
# frozenset field, by an empty spec or by !s, !r or !a with any plain
# spec, take the container's repr, calling its items' Python __repr__,
# which may loop, in order, also inside nested containers and keyword
# fields; !a escapes the text, and the spec then formats it. A container
# whose repr is being built shows as [...]; an exception from __repr__
# propagates. Inside functions as at module level.
from harness import *

log = []

class R:
    def __init__(self, t): self.t = t
    def __hash__(self): return 1
    def __repr__(self):
        for _ in (): pass
        log.append(self.t)
        if self.t == "self": return "{!r}|{}".format(outer, outer)
        if self.t == "bad": raise LookupError("r")
        return "Ré" + self.t

outer = []
outer.append(R("self"))

def run():
    for _ in (): pass
    return ["{!r}".format([R("a")]), "{}|{!s:>9}".format((R("b"), 1), [R("c")]), "{0!a}".format({1: R("d")}),
            "{k}".format(k={R("e")}), "{x!r:^11}".format_map({"x": frozenset([R("f")])}), "{}".format([[R("g")], (R("h"),)]),
            "{!r}".format(outer), "{}".format([1, 2])]

expected = ["[Réa]", "(Réb, 1)|    [Réc]", "{1: R\\xe9d}", "{Rée}", "frozenset({Réf})", "[[Rég], (Réh,)]", "[[...]|[...]]", "[1, 2]"]
expected_log = ["a", "b", "c", "d", "e", "f", "g", "h", "self"]
assert_eq(run(), expected)
assert_eq(log, expected_log)
log.clear()

assert_eq(["{!r}".format([R("a")]), "{}|{!s:>9}".format((R("b"), 1), [R("c")])], expected[:2])
assert_eq(log, expected_log[:3])
log.clear()

def errors():
    for _ in (): pass
    try: "{}{}".format([R("a"), R("bad"), R("c")], [R("d")])
    except LookupError as e: return e.args, log

assert_eq(errors(), (("r",), ["a", "bad"]))
