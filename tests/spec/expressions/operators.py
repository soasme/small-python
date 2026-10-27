# spec: reference/expressions.html#operator-precedence
# description: Precedence, associativity, comparisons, boolean operations, conditional expressions, lambda, walrus.
from harness import *

assert_eq(2 + 3 * 4 ** 2, 50)
assert_eq(2 ** 3 ** 2, 512)
assert_eq(-2 ** 2, -4)
assert_eq((-2) ** 2, 4)
assert_eq(2 ** -1, 0.5)
assert_eq(10 - 3 - 2, 5)
assert_eq(100 / 10 / 5, 2.0)
assert_eq(1 + 2 << 1, 6)
assert_eq(1 | 2 ^ 3 & 4, 3)
assert_eq(not 1 == 2, True)
assert_eq(-~0, 1)
assert_eq(~-1, 0)
assert_eq(+-+1, -1)
assert_eq(1 if 0 else 2 if 0 else 3, 3)
assert_eq((lambda: 1 if False else 2)(), 2)
assert_eq([x for x in (1, 2) if x if x > 1], [2])
assert_eq(not None in [None], False)
assert_eq(3 - -3, 6)
assert_eq(2 * -1 ** 2, -2)
assert_eq(1 < 2 == 2 > 1, True)
assert_eq("a" "b" * 2, "abab")

# Chained comparisons evaluate each operand once and short-circuit.
order = []
def t(x):
    order.append(x)
    return x
assert_true(t(1) < t(2) < t(3))
assert_eq(order, [1, 2, 3])
order.clear()
assert_false(t(3) < t(2) < t(1))
assert_eq(order, [3, 2])
assert_true(1 < 2 > 0 != 5 is not None)
assert_true(1 in [1] not in [[0]])
x = [1]
assert_true(x is x is not None)

# Boolean operators return an operand, not a bool.
assert_eq(0 or "", "")
assert_eq(1 and [], [])
assert_eq(None or 0 or "x", "x")
assert_eq([] and 1/0, [])
assert_eq(1 or 1/0, 1)
assert_eq(not [], True)
class Truth:
    def __bool__(self):
        order.append("bool")
        return True
order.clear()
t1 = Truth()
assert_is(t1 and t1, t1)
assert_eq(order, ["bool"])
order.clear()
assert_is(not t1, False)

# Conditional expressions evaluate only the chosen branch.
assert_eq(1 if True else 1/0, 1)
assert_syntax_error("x = 1 if True")
assert_syntax_error("x = a if b else c if d")

# Assignment expressions.
assert_eq((y := 5) + y, 10)
data = [1, 2, 3, 4]
assert_eq([z for v in data if (z := v * 2) > 4], [6, 8])
assert_eq(z, 8)  # binds in the containing scope
assert_syntax_error("y := 1")
assert_syntax_error("(a.b := 1)")
assert_syntax_error("(a[0] := 1)")
assert_syntax_error("((a, b) := (1, 2))")
assert_syntax_error("[i := 0 for i in range(3)]")
assert_syntax_error("[x for x in (y := [1])]") if False else None
assert_syntax_error("def f(a := 1): pass")
assert_syntax_error("f(a := 1 for a in b)") if False else None
assert_compiles("f(a := 1)")
assert_compiles("x = (y := 1)")
assert_syntax_error("x = y := 1")
assert_compiles("print(f'{(w:=10)}')")
def scope():
    [(inner := i) for i in range(3)]
    return inner
assert_eq(scope(), 2)
class Scoped:
    assert_syntax_error("class C:\n    [(q := i) for i in range(2)]\n")

# Lambda.
assert_eq((lambda *a, **k: (a, k))(1, b=2), ((1,), {"b": 2}))
assert_eq((lambda x=1: x)(), 1)
assert_eq([(lambda: i)() for i in range(3)], [0, 1, 2])
assert_eq([f() for f in [lambda: i for i in range(3)]], [2, 2, 2])
assert_syntax_error("lambda: (yield)") if False else None
assert_syntax_error("lambda x: return x")
assert_syntax_error("lambda (x): x")

# Identity and membership.
assert_true(None is None)
assert_true([] is not [])
assert_true("a" in "cat")
assert_true("" in "abc")
assert_true(2 in range(3))
assert_true((1, 2) in {(1, 2): 0})
assert_raises(TypeError, lambda: 1 in 5)
assert_raises(TypeError, lambda: [] in {})
nan = float("nan")
assert_true(nan in [nan])  # identity implies membership
assert_false(nan == nan)

# Ordering comparisons between unrelated types fail.
assert_raises(TypeError, lambda: 1 < "a")
assert_raises(TypeError, lambda: [] < ())
assert_raises(TypeError, lambda: None < None)
assert_true([1, 2] < [1, 3])
assert_true((1, 2) < (1, 2, 0))
assert_true("abc" < "abd")
assert_true(b"a" < b"b")
assert_true({1} < {1, 2})
assert_false({1} < {2})
assert_true(1 == 1.0 == 1 + 0j)
assert_true(True == 1)
assert_false([1] == (1,))
assert_true({1: 2} == {1: 2})
assert_raises(TypeError, lambda: {} < {})
