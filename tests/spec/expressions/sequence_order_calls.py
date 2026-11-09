# spec: PLS-315 13.10.1, 25.5.3
# description: Ordering two lists or two tuples compares their items in
# order by ==, an item never with itself, until a pair is unequal; that
# pair's ordering, by its Python method, its reflected one after
# NotImplemented, is the result, which need not be a bool; with no such
# pair the lengths decide. An item's __eq__ is called once per pair and
# again inside a nested sequence it belongs to; an exception from either
# method propagates, and a list an __eq__ shortens ends the comparison by
# the lengths, in a lone test, an if, a chain and an assignment, inside
# functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class P:
    def __init__(self, v): self.v = v
    def __eq__(self, other):
        spin()
        log.append(("eq", self.v, other.v))
        if self.v == 7: raise KeyError(7)
        return self.v == other.v
    def __lt__(self, other):
        spin()
        log.append(("lt", self.v, other.v))
        return "less" if self.v < other.v else ""
    def __gt__(self, other):
        spin()
        log.append(("gt", self.v, other.v))
        return NotImplemented

class Plain:
    def __init__(self, v): self.v = v
    def __lt__(self, other):
        spin()
        log.append(("plain", self.v, other.v))
        return self.v < other.v

class Shrinking(P):
    def __eq__(self, other):
        del victim[1:]
        return True

victim = []

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    global victim
    del log[:]
    a, b = P(1), P(2)
    out = [(0, a) < (0, b), [a, 1] < [a, 2], (a, b) <= (a,), (a,) < (a, b), ((a, 1),) < ((P(1), 2),)]
    out.append((Plain(1), 5) < (Plain(2), 0))
    out.append(error(lambda: (P(7), 1) < (P(1), 2)))
    out.append((a,) > (b,))
    if (b, 0) < (a, 1): out.append("taken")
    else: out.append("not taken")
    out.append((P(0),) < (a,) < (b,))
    if [P(5)] < [P(5), 0]: out.append("shorter")
    if (Plain(3), spin()) < (Plain(4), 0): out.append("plain")
    victim = [P(3), P(4), P(5)]
    out.append(victim < [Shrinking(3), P(9), P(9)])
    out.append(list(log))
    return out

expected = ["less", True, False, True, True, True, ("KeyError", "7"), "", "not taken", "less", "shorter", "plain", True,
            [("eq", 1, 2), ("lt", 1, 2), ("eq", 1, 1), ("eq", 1, 1), ("plain", 1, 2), ("eq", 7, 1), ("eq", 1, 2),
             ("gt", 1, 2), ("lt", 2, 1), ("eq", 2, 1), ("lt", 2, 1), ("eq", 0, 1), ("lt", 0, 1), ("eq", 1, 2),
             ("lt", 1, 2), ("eq", 5, 5), ("plain", 3, 4)]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
