# spec: PLS-315 7.2.4, 25.5.3
# description: A list or tuple compared with an instance of a subclass of
# list or tuple whose class defines no comparison, either way round,
# compares their items as the list or tuple: the items' Python __eq__,
# which may loop, in order, with the subclass instance's items first when
# it is the right operand of its base's object, then for an ordering the
# first unequal pair's Python method; a method's exception propagates.
# Inside functions as at module level.
from harness import *

log = []

class Item:
    def __init__(self, v): self.v = v
    def __eq__(self, other):
        for _ in range(2): pass
        log.append(("eq", self.v, getattr(other, "v", other)))
        if self.v == "bad": raise LookupError("eq")
        return isinstance(other, Item) and self.v == other.v
    def __lt__(self, other):
        log.append(("lt", self.v, other.v))
        return self.v < other.v
    __hash__ = None

class L(list): pass
class T(tuple): pass

def error(f):
    try:
        return f()
    except LookupError as e:
        return str(e)

def compares():
    del log[:]
    a, b = [Item(1), Item(2)], L([Item(1), Item(3)])
    p, q = (Item(1), Item(2)), T((Item(1), Item(3)))
    out = [a == b, b == a, a != b, b != a, a < b, b < a, p == q, q == p, p < q, q > p, a == L(a), b > a]
    out.append(error(lambda: [Item("bad")] == L([Item(0)])))
    out.append(error(lambda: L([Item("bad")]) == [Item(0)]))
    out.append(L() == [] and T() == () and not (L([1]) == [2]))
    return out + [list(log)]

expected = [False, False, True, True, True, False, False, False, True, True, True, True, False, 'eq', True,
             [('eq', 1, 1), ('eq', 3, 2), ('eq', 1, 1), ('eq', 3, 2), ('eq', 1, 1), ('eq', 3, 2), ('eq', 1, 1),
             ('eq', 3, 2), ('eq', 1, 1), ('eq', 3, 2), ('lt', 2, 3), ('eq', 1, 1), ('eq', 3, 2), ('lt', 3, 2),
             ('eq', 1, 1), ('eq', 3, 2), ('eq', 1, 1), ('eq', 3, 2), ('eq', 1, 1), ('eq', 3, 2), ('lt', 2, 3),
             ('eq', 1, 1), ('eq', 3, 2), ('lt', 2, 3), ('eq', 1, 1), ('eq', 3, 2), ('lt', 2, 3), ('eq', 0, 'bad'),
             ('eq', 'bad', 0)]]

def main():
    return compares()

assert_eq(main(), expected)
assert_eq(compares(), expected)
