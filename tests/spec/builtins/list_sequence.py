# spec: PLS-315 25.1, 25.5
# description: Lists as sequences: indexing, slicing, concatenation, and mutation.
from harness import *
squares = [1, 4, 9, 16, 25]

assert 1 == squares[0]
assert 25 == squares[-1]
assert [9, 16, 25] == squares[-3:]
assert squares == squares[:]

assert [1, 9, 25] == squares[::2]
assert [4, 16] == squares[1::2]
assert [4] == squares[1:2:2]
assert [25] == squares[4:100]

squares_tuple = (1, 4, 9, 16, 25)

assert 1 == squares_tuple[0]
assert 25 == squares_tuple[-1]
assert (9, 16, 25) == squares_tuple[-3:]
assert squares_tuple == squares_tuple[:]

assert (1, 9, 25) == squares_tuple[::2]
assert (4, 16) == squares_tuple[1::2]
assert (4,) == squares_tuple[1:2:2]
assert (25,) == squares_tuple[4:100]
l = [1, 2, 3]
assert [1, 2, 3, 4, 5] == (l + [4, 5])
x = [1, 999, 3]
x[1] = 2
assert [1, 2, 3] == x
