# spec: PLS-315 19.3.24, 7.5.2
# description: len() and __len__ results.
from harness import *
assert 3 == len([1, 2, 3])
assert 2 == len((1, 2))
