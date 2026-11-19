# spec: PLS-315 27.1.6 7.5.6 7.5.5
# description: map() of repr, str or ascii over containers holding
# instances calls each instance's Python __repr__ once per item, in
# order, for the container's repr; an error in one propagates out of the
# map, and a container that holds itself shows as an ellipsis.
from harness import *

log = []
class R:
    def __init__(self, tag): self.tag = tag
    def __repr__(self):
        for _ in (): pass
        log.append(self.tag)
        if self.tag == "bad": raise KeyError("bad")
        return "R" + self.tag

def results():
    del log[:]
    me = [R("m")]
    me.append(me)
    out = [list(map(repr, [[R("a"), R("b")], (R("c"),), {R("d"): R("e")}])), list(map(str, [[R("f")]])),
           list(map(ascii, [[R("g")]])), list(map(repr, [me]))]
    try: out.append(list(map(repr, [[R("h"), R("bad"), R("i")]])))
    except KeyError as e: out.append(("KeyError", str(e)))
    return out, list(log)

expected = ([["[Ra, Rb]", "(Rc,)", "{Rd: Re}"], ["[Rf]"], ["[Rg]"], ["[Rm, [...]]"], ("KeyError", "'bad'")],
            ["a", "b", "c", "d", "e", "f", "g", "m", "h", "bad"])

assert_eq(results(), expected)
assert_eq(results(), expected)
