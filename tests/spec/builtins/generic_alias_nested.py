# spec: PLS-315 29.9.2, 29.9.3
# description: A generic alias substitutes its parameters inside list and
# tuple arguments at any depth, each keeping its kind; parameters are
# collected and found by identity, so equal parameters stay distinct; an
# unpacked TypeVarTuple-like argument's substitution must be a tuple. A list
# argument's repr reads its length once, so an item that shrinks the list
# makes the repr raise IndexError.
from harness import *

def f[U, V](): pass
U, V = f.__type_params__
type A[**P, T] = int
nested = A[[U, [V], int], V]
assert_eq(nested.__parameters__, (U, V))
assert_eq(nested[str, float].__args__, ([str, [float], int], float))
assert_eq(dict[U, [[U, (U,)]]][int].__args__, (int, [[int, (int,)]]))
assert_eq(type(dict[U, [(U,)]][int].__args__[1][0]), tuple)

class Same:
    def __eq__(self, other): return True
    __hash__ = object.__hash__
    def __typing_subst__(self, arg): return ("sub", arg)
a, b = Same(), Same()
pair = dict[a, b]
assert_true(pair.__parameters__[0] is a and pair.__parameters__[1] is b)
assert_eq(pair[int, str].__args__, (("sub", int), ("sub", str)))

class Unpacked:
    __typing_is_unpacked_typevartuple__ = True
    def __typing_subst__(self, arg): return 5
try:
    list[Unpacked()][int]
except TypeError as e:
    assert_eq(str(e), "expected __typing_subst__ of Unpacked objects to return a tuple, not int")
else:
    raise AssertionError("no TypeError")

GA = type(list[int])
items = []
class Shrinks:
    def __repr__(self):
        items.clear()
        return "x"
items += [Shrinks(), 1]
assert_raises(IndexError, repr, GA(int, items))
assert_eq(repr(GA(int, [Shrinks()])), "int[[x]]")
