# spec: PLS-315 7.7.7
# description: a class whose __length_hint__ is a builtin method bound to
# another object has it called with no arguments when list, bytes or
# unpacking asks the length hint; its exception propagates, tuple asks
# none, and it runs once per request.
from harness import assert_eq, assert_raises

class X:
    def __iter__(self): return iter([1, 2])
    __length_hint__ = [].pop

for make in (list, bytes, lambda x: [*x]):
    assert_eq(str(assert_raises(IndexError, make, X())), "pop from empty list")
assert_eq(tuple(X()), (1, 2))

src = [7, 3]
class Y:
    def __iter__(self): return iter([1])
    __length_hint__ = src.pop

assert_eq((list(Y()), src), ([1], [7]))
