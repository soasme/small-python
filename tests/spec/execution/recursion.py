# spec: PLS-315 9.6, B.6
# description: Calls and reprs past the recursion limit raise RecursionError instead of starting.
from harness import *

def down(n):
    return down(n + 1)
e = assert_raises(RecursionError, down, 0)
assert_true(str(e).startswith("maximum recursion depth exceeded"), str(e))

class R:
    def __repr__(self):
        return repr(self)
assert_raises(RecursionError, repr, R())

# Deeply nested data fails safely.
nested = []
for _ in range(200000):
    nested = [nested]
assert_raises(RecursionError, repr, nested)
e = assert_raises((RecursionError, MemoryError, SyntaxError), eval, "(" * 200000 + ")" * 200000)

# The program recovers: the depth is released as frames complete.
def depth(n):
    return 0 if n == 0 else 1 + depth(n - 1)
assert_eq(depth(host.recursion_limit() // 2), host.recursion_limit() // 2)
