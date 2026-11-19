# spec: PLS-315 7.2.4, 13.10.1, 25.5.3
# description: an ordering of a list or tuple and an instance of its
# subclass that defines no comparison of its own, the subclass instance on
# the right, is that instance's reflected ordering: its items are compared
# first, by __eq__ from its side, then the first unequal pair by the
# reflected operator, whose Python methods may loop and return any
# object; equal items leave the lengths to decide, NotImplemented falls
# back to the other item's method, and an error propagates. Inside
# functions and generators as at module level.
from harness import *

log = []
class V:
    def __init__(self, v): self.v = v
    def __eq__(self, o):
        for _ in (): pass
        log.append(("eq", self.v, o.v))
        return self.v == o.v
    def __lt__(self, o):
        for _ in (): pass
        log.append(("lt", self.v, o.v))
        return "less" if self.v < o.v else ""
    def __gt__(self, o):
        for _ in (): pass
        log.append(("gt", self.v, o.v))
        if self.v == 9: return NotImplemented
        if self.v == 8: raise KeyError("gt")
        return "more" if self.v > o.v else ""
class L(list): pass
class T(tuple): pass

def order(x, y, op):
    del log[:]
    try: r = x < y if op == "<" else x > y
    except KeyError: r = "KeyError"
    return r, list(log)

def cases():
    return [order([V(1), V(2)], L([V(1), V(3)]), "<"),
            order((V(1), V(2)), T((V(1), V(3))), ">"),
            order([V(2)], L([V(1)]), ">"),
            order([V(1)], L([V(9)]), "<"),
            order([V(1)], L([V(8)]), "<"),
            order([V(1)], L([V(1), V(5)]), ">"),
            order(L([V(1), V(2)]), [V(1), V(3)], "<")]

expected = [("more", [("eq", 1, 1), ("eq", 3, 2), ("gt", 3, 2)]),
            ("", [("eq", 1, 1), ("eq", 3, 2), ("lt", 3, 2)]),
            ("less", [("eq", 1, 2), ("lt", 1, 2)]),
            ("less", [("eq", 9, 1), ("gt", 9, 1), ("lt", 1, 9)]),
            ("KeyError", [("eq", 8, 1), ("gt", 8, 1)]),
            (False, [("eq", 1, 1)]),
            ("less", [("eq", 1, 1), ("eq", 2, 3), ("lt", 2, 3)])]
assert_eq(cases(), expected)

def gen():
    yield cases()
assert_eq(next(gen()), expected)
