# spec: reference/expressions.html#arithmetic-conversions
# description: Mixed int/float/complex operands are converted to the wider type.
from harness import *

assert_same(1 + 2.0, 3.0)
assert_same(2.0 * 3, 6.0)
assert_same(1 + 2j, complex(1, 2))
assert_same(1.5 + 1j, complex(1.5, 1))
assert_same(True + 1, 2)
assert_same(True + 1.0, 2.0)
assert_same(True + True, 2)
assert_same(False * 3j, 0j)
assert_same(7 / 2, 3.5)
assert_same(8 / 2, 4.0)
assert_same(2 ** -1, 0.5)
assert_same(2 ** 3, 8)
assert_same((-8) ** (1 / 3), complex(1.0000000000000002, 1.7320508075688772))
assert_same(10 % 3.0, 1.0)
assert_same(divmod(7, 2), (3, 1))
assert_same(divmod(7.0, 2), (3.0, 1.0))
# bool is a subclass of int; arithmetic on bools gives ints.
assert_same(-True, -1)
assert_same(~False, -1)
assert_same(True & False, False)
assert_same(True | 2, 3)
