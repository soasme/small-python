# spec: PLS-315 25.5.2 7.5.4
# description: A sequence's explicit __mul__, __rmul__ or __imul__ takes
# its count by the count's Python __index__, called once, then repeats as
# the operator does; an error of __index__ propagates, a result that is
# no int raises TypeError, and a self of another type is refused before
# __index__ is called.
from harness import *

log = []
class N:
    def __init__(self, n): self.n = n
    def __index__(self):
        for _ in (): pass
        log.append(self.n)
        if self.n == "bad": raise KeyError("bad")
        return self.n

def attempt(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))

def results():
    del log[:]
    s = [1]
    out = [[1].__mul__(N(2)), (1,).__rmul__(N(2)), "ab".__mul__(N(2)), b"a".__rmul__(N(3)), bytearray(b"x").__mul__(N(2)),
           s.__imul__(N(3)) is s, s, list.__mul__([0], N(2)), attempt(lambda: [1].__mul__(N("bad"))),
           attempt(lambda: [1].__mul__(N("x"))), attempt(lambda: list.__mul__((1,), N(5))), [2].__mul__(N(True))]
    return out, list(log)

expected = ([[1, 1], (1, 1), "abab", b"aaa", bytearray(b"xx"), True, [1, 1, 1], [0, 0], ("KeyError", "'bad'"),
             ("TypeError", "N.__index__() must return an int, not str"),
             ("TypeError", "descriptor '__mul__' requires a 'list' object but received a 'tuple'"), [2]],
            [2, 2, 2, 3, 2, 3, 2, "bad", "x", True])

assert_eq(results(), expected)
assert_eq(results(), expected)
