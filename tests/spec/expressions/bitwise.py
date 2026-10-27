# spec: PLS-315 13.8, 13.9, 7.6.2
# description: Shifts and the bitwise operators: precedence, grouping, dispatch, and errors.
from harness import *

assert_eq(1 << 4, 16)
assert_eq(256 >> 4, 16)
assert_eq(-1 >> 10, -1)
assert_eq(-16 >> 2, -4)
assert_eq(1 << 100, 1267650600228229401496703205376)
assert_eq(1 << 2 + 1, 8)        # + binds tighter than <<
assert_eq(1 << 2 << 3, 32)      # left to right
assert_eq(6 & 3, 2)
assert_eq(6 ^ 3, 5)
assert_eq(6 | 3, 7)
assert_eq(1 | 2 ^ 3 & 4, 3)     # & then ^ then |
assert_eq(1 | 6 & 3, 3)
assert_eq(-6 & 0xFF, 250)
assert_eq(~5, -6)
assert_eq(True & False, False)
assert_type(True | False, bool)
assert_type(True ^ 1, int)
assert_eq({1, 2} & {2, 3}, {2})
assert_eq({1, 2} | {2, 3}, {1, 2, 3})
assert_eq({1, 2} ^ {2, 3}, {1, 3})
e = assert_raises(ValueError, lambda: 1 << -1)
assert_eq(str(e), "negative shift count")
e = assert_raises(ValueError, lambda: 1 >> -1)
assert_eq(str(e), "negative shift count")
e = assert_raises(TypeError, lambda: 1.0 << 1)
assert_eq(str(e), "unsupported operand type(s) for <<: 'float' and 'int'")
e = assert_raises(TypeError, lambda: 1.0 & 1)
assert_eq(str(e), "unsupported operand type(s) for &: 'float' and 'int'")

class B:
    def __lshift__(self, o): return "lshift"
    def __rrshift__(self, o): return "rrshift"
    def __and__(self, o): return "and"
    def __rxor__(self, o): return "rxor"
    def __or__(self, o): return NotImplemented
    def __ror__(self, o): return "ror"
assert_eq(B() << 1, "lshift")
assert_eq(1 >> B(), "rrshift")
assert_eq(B() & 1, "and")
assert_eq(1 ^ B(), "rxor")
assert_eq(1 | B(), "ror")
e = assert_raises(TypeError, lambda: B() | 1)
assert_eq(str(e), "unsupported operand type(s) for |: 'B' and 'int'")
