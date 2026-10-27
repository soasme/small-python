# spec: PLS-315 13.2.6
# description: Comprehension scoping, clause order, filtering, unpacking, and errors.
from harness import *

assert_eq([x * y for x in range(3) for y in range(x)], [0, 0, 2])
assert_eq([x for x in range(10) if x % 2 if x > 3], [5, 7, 9])
assert_eq({x % 3 for x in range(10)}, {0, 1, 2})
assert_eq({x: x * x for x in range(3)}, {0: 0, 1: 1, 2: 4})
assert_eq([(a, b) for a, b in [(1, 2), (3, 4)]], [(1, 2), (3, 4)])
assert_eq([[y for y in range(x)] for x in range(3)], [[], [0], [0, 1]])

# The iteration variable does not leak; the comprehension has its own scope.
x = "outer"
[x for x in range(3)]
assert_eq(x, "outer")

# The first iterable is evaluated in the enclosing scope, the rest in the comprehension scope.
class C:
    values = [1, 2]
    doubled = [v * 2 for v in values]
    try:
        bad = [v for v in range(1) for w in values]
    except NameError:
        bad = "NameError"
assert_eq(C.doubled, [2, 4])
assert_eq(C.bad, "NameError")

# The first iterable is evaluated immediately, even for generator expressions.
def boom():
    raise ZeroDivisionError
assert_raises(ZeroDivisionError, lambda: (x for x in boom()))
g = (1 / 0 for x in range(1))
assert_raises(ZeroDivisionError, next, g)

# PEP 798 unpacking in comprehensions (3.15): *expr in list/set/genexp, **expr in dict.
lists = [[1, 2], [3], []]
assert_eq([*l for l in lists], [1, 2, 3])
assert_eq({*l for l in lists}, {1, 2, 3})
assert_eq(list(*l for l in lists), [1, 2, 3])
dicts = [{"a": 1}, {"b": 2}, {"a": 3}]
assert_eq({**d for d in dicts}, {"a": 3, "b": 2})
assert_syntax_error("[**d for d in x]")
assert_syntax_error("{*a: 1 for a in x}")

# Assignment expressions bind in the containing scope.
[last := n for n in range(4)]
assert_eq(last, 3)
assert_syntax_error("[i := 0 for i in range(3)]")
assert_syntax_error("[x for x in (y := [1])]")
assert_syntax_error("class A:\n    [(z := 1) for _ in range(2)]")

# yield and await are not allowed inside comprehensions.
assert_syntax_error("def f():\n    [(yield x) for x in y]")
assert_syntax_error("def f():\n    [x async for x in y]")
assert_syntax_error("[x for x in 1 2]")
assert_syntax_error("[x, y for x in z]")

# Order of evaluation of clauses.
log = []
def it(name, values):
    log.append(name)
    return values
[(a, b) for a in it("A", [1, 2]) for b in it("B", [3])]
assert_eq(log, ["A", "B", "B"])
