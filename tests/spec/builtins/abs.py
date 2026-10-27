# spec: library/functions.html#abs
# description: abs() of ints, floats, bools, and objects with __abs__.
from harness import *
assert abs(-3) == 3
assert abs(7) == 7
assert abs(-3.21) == 3.21
assert abs(6.25) == 6.25
