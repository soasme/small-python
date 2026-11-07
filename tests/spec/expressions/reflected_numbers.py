# spec: PLS-315 13.7, 13.10, 7.4.3
# description: A number with a plain instance on its right: the number's
# own operator declines, so the instance's reflected method, which may
# loop, is called with the number, inside functions as at module level,
# for binary operators, augmented assignments and comparisons; when it
# declines too, the operator raises TypeError and == falls back to identity.
from harness import *

log = []

class Vector:
    def __init__(self, *items): self.items = items
    def __rmul__(self, k):
        for _ in range(2): pass
        log.append(("rmul", k))
        return Vector(*(k * x for x in self.items))
    def __radd__(self, k):
        log.append(("radd", k))
        return NotImplemented if k == 0 else k + sum(self.items)
    def __gt__(self, k):
        log.append(("gt", k))
        return sum(self.items) > k
    def __eq__(self, k):
        log.append(("eq", k))
        return NotImplemented

def operations():
    del log[:]
    v = Vector(1, 2)
    out = [(2 * v).items, (2.5 * v).items, (True * v).items, 10 + v]
    try:
        0 + v
    except TypeError as e:
        out.append(str(e))
    n = 5
    n += v
    out.append(n)
    try:
        n = 0
        n += v
    except TypeError as e:
        out.append(str(e))
    out += [1 < v, 5 < v, 3 == v, 3 != v]
    try:
        1 - v
    except TypeError as e:
        out.append(str(e))
    out.append(list(log))
    return out

expected = [(2, 4), (2.5, 5.0), (1, 2), 13,
            "unsupported operand type(s) for +: 'int' and 'Vector'",
            8, "unsupported operand type(s) for +=: 'int' and 'Vector'",
            True, False, False, True,
            "unsupported operand type(s) for -: 'int' and 'Vector'",
            [("rmul", 2), ("rmul", 2.5), ("rmul", True), ("radd", 10), ("radd", 0), ("radd", 5), ("radd", 0),
             ("gt", 1), ("gt", 5), ("eq", 3), ("eq", 3)]]
assert_eq(operations(), expected)
assert_eq((3 * Vector(1)).items, (3,))
