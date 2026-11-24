# spec: PLS-315 7.6.2, 7.6.3
# description: once x's and y's methods decline, x * y repeats x when x
# keeps its own repetition and otherwise repeats y by x, by its __index__;
# x *= y repeats y by x only when x's type has no sequence methods, which
# every class but the builtin ones has; in functions and at module level.
from harness import assert_eq
def error(f):
    try:
        return f()
    except TypeError as e:
        return str(e)
def augment(x, y):
    x *= y
    return x
class Count:
    def __index__(self): return 2
class Declining:
    def __mul__(self, o): return NotImplemented
    def __index__(self): return 3
class S(str):
    def __mul__(self, o): return NotImplemented
class SI(S):
    def __index__(self): return 3
class I(int): pass
class Meta(type): pass
class K(metaclass=Meta): pass
assert_eq([error(lambda: S('a') * 'b'), error(lambda: SI('a') * 'b'), error(lambda: Declining() * [1]),
           error(lambda: Count() * 'b'), error(lambda: 'b' * Count())],
          ["can't multiply sequence by non-int of type 'S'", 'bbb', [1, 1, 1], 'bb', 'bb'])
assert_eq([error(lambda: augment(S('a'), 'b')), error(lambda: augment(SI('a'), 'b')), error(lambda: augment(Count(), 'b')),
           error(lambda: augment(Declining(), [1])), error(lambda: augment(I(2), 'b')), error(lambda: augment(K, 'b'))],
          ["unsupported operand type(s) for *=: 'S' and 'str'", "unsupported operand type(s) for *=: 'SI' and 'str'",
           "unsupported operand type(s) for *=: 'Count' and 'str'", "unsupported operand type(s) for *=: 'Declining' and 'list'",
           "unsupported operand type(s) for *=: 'I' and 'str'", "unsupported operand type(s) for *=: 'Meta' and 'str'"])
for x in ({}, set(), frozenset(), range(1), {}.keys(), {}.values(), {}.items(), memoryview(b''), type.__dict__, frozendict()):
    assert_eq(error(lambda: augment(x, 'b')), "unsupported operand type(s) for *=: '%s' and 'str'" % type(x).__name__)
for x in (None, 1.0, object(), len, slice(1), int, ...):
    assert_eq(error(lambda: augment(x, 'b')), "can't multiply sequence by non-int of type '%s'" % type(x).__name__)
assert_eq((augment(2, 'b'), augment(I(2), 3), augment(True, [1])), ('bb', 6, [1]))
x = Count()
try:
    x *= 'b'
except TypeError as e:
    assert_eq(str(e), "unsupported operand type(s) for *=: 'Count' and 'str'")
x = 'b'
x *= Count()
assert_eq(x, 'bb')
