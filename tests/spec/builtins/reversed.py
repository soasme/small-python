# spec: library/functions.html#reversed
# description: reversed() of sequences and __reversed__.
from harness import *
assert list(reversed(range(5))) == [4, 3, 2, 1, 0]

l = [5, 4, 3, 2, 1]
assert list(reversed(l)) == [1, 2, 3, 4, 5]
