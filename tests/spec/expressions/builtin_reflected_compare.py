# spec: PLS-315 7.2.4, 13.10
# description: None, a str, bytes, tuple, list or dict, and an instance
# whose class compares as object does, decline a rich comparison with an
# instance of another class, which the instance's reflected method then
# decides: its value is the comparison's, whatever it is; a NotImplemented
# leaves == and != to identity and an ordering to TypeError, and an
# exception propagates, in a lone test, an if, a chain and a not, inside
# functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class R:
    def __init__(self, v): self.v = v
    def __eq__(self, other):
        spin()
        log.append(("eq", self.v, type(other).__name__))
        if self.v == "raise": raise KeyError("eq")
        return NotImplemented if self.v == "decline" else self.v
    def __gt__(self, other):
        spin()
        log.append(("gt", self.v, type(other).__name__))
        return NotImplemented if self.v == "decline" else self.v
    def __le__(self, other):
        spin()
        log.append(("le", self.v, type(other).__name__))
        return "le"

class Bare:
    pass

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    r, d, bare = R("yes"), R("decline"), Bare()
    out = [None == r, "a" == r, b"a" != r, (1,) == r, [1] == r, {} == r, bare == r, "a" < r, (1,) >= r]
    out += [None == d, "a" != d, bare == d, error(lambda: "a" < d), error(lambda: [] < d), error(lambda: "a" == R("raise"))]
    if "a" == r: out.append("taken")
    out.append(not ("a" == R("")))
    out.append("a" < r <= "z")
    out.append(list(log))
    return out

expected = ["yes", "yes", False, "yes", "yes", "yes", "yes", "yes", "le", False, True, False,
            ("TypeError", "'<' not supported between instances of 'str' and 'R'"),
            ("TypeError", "'<' not supported between instances of 'list' and 'R'"), ("KeyError", "'eq'"), "taken", True, "le",
            [("eq", "yes", "NoneType"), ("eq", "yes", "str"), ("eq", "yes", "bytes"), ("eq", "yes", "tuple"),
             ("eq", "yes", "list"), ("eq", "yes", "dict"), ("eq", "yes", "Bare"), ("gt", "yes", "str"), ("le", "yes", "tuple"),
             ("eq", "decline", "NoneType"), ("eq", "decline", "str"), ("eq", "decline", "Bare"), ("gt", "decline", "str"),
             ("gt", "decline", "list"), ("eq", "raise", "str"), ("eq", "yes", "str"), ("eq", "", "str"), ("gt", "yes", "str"),
             ("le", "yes", "str")]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
