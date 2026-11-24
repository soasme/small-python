# spec: PLS-315 7.2.4, 26.1.2
# description: == and != of a dict or frozendict subclass's instance whose
# class keeps the builtin comparison and another dict compare their
# entries, each value's Python __eq__ called, which may loop, return a
# non-bool or raise, as a list subclass's do; the subclass's instance on the right goes first,
# its values on the left (a frozendict's under a dict's does not), and a class's Python __eq__ comes before both.
from harness import *

log = []
class E:
    def __init__(self, name): self.name = name
    def __eq__(self, other):
        for _ in range(2): pass
        log.append(self.name)
        if self.name == "raise": raise LookupError("eq")
        return self.name != "no"
class S(dict): pass
class F(frozendict): pass
class Own(dict):
    def __eq__(self, other):
        for _ in range(2): pass
        log.append("own")
        return NotImplemented
class OwnList(list):
    def __eq__(self, other):
        for _ in range(2): pass
        log.append("own")
        return NotImplemented
def run(f):
    del log[:]
    try:
        return f(), log[:]
    except Exception as e:
        return type(e).__name__, log[:]

def cases():
    return [run(lambda: S(k=E("s")) == {"k": E("d")}), run(lambda: {"k": E("d")} == S(k=E("s"))),
            run(lambda: S(k=E("no")) != S(k=E("t"))), run(lambda: F(k=E("f")) == frozendict(k=E("g"))),
            run(lambda: {"k": E("d")} == F(k=E("f"))), run(lambda: S(k=E("raise")) == {"k": 1}),
            run(lambda: Own(k=E("o")) == {"k": E("d")}), run(lambda: S(a=1) == {"b": E("x")}),
            run(lambda: OwnList([E("o")]) == [E("d")]), run(lambda: Own() == OwnList())]
expected = [(True, ["s"]), (True, ["s"]), (True, ["no"]), (True, ["f"]), (True, ["d"]),
            ("LookupError", ["raise"]), (True, ["own", "d"]), (False, []),
            (True, ["own", "d"]), (False, ["own", "own"])]
assert_eq(cases(), expected)
def gen():
    yield cases()
assert_eq(next(gen()), expected)
