# spec: library/functions.html#len
# description: len() and __len__ results.
from harness import *
assert 3 == len([1, 2, 3])
assert 2 == len((1, 2))
