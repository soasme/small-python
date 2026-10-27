# spec: PLS-315 13.12, 8.6
# description: name := e binds in the enclosing scope and returns the value; where it may appear.
from harness import *

assert_eq((x := 5), 5)
assert_eq(x, 5)
if (n := len([1, 2, 3])) > 2:
    assert_eq(n, 3)
values = [y := 1, y + 1]
assert_eq(values, [1, 2])

# In a comprehension the target binds in the containing scope.
def f():
    [last := i for i in range(3)]
    return last
assert_eq(f(), 2)
total = 0
assert_eq([total := total + i for i in range(4)], [0, 1, 3, 6])
assert_eq(total, 6)

# Each use is evaluated where it stands, left to right.
assert_eq([(a := 1), a + 1, (a := 10), a], [1, 2, 10, 10])

for source in ("x := 1\n", "y = x := 1\n", "y: int = x := 1\n", "f(k=x := 1)\n", "def g(a=x := 1): pass\n"):
    assert_eq(assert_syntax_error(source).msg, "invalid syntax", source)
assert_compiles("(x := 1)\ny = (x := 1)\nf(k=(x := 1))\nf(x := 1)\n")
assert_eq(assert_syntax_error("(a.b := 1)\n").msg, "cannot use assignment expressions with attribute")
assert_eq(assert_syntax_error("(a[0] := 1)\n").msg, "cannot use assignment expressions with subscript")
assert_eq(assert_syntax_error("((a, b) := 1)\n").msg, "cannot use assignment expressions with tuple")
