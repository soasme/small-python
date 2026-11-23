# spec: PLS-315 8.3.1, 8.6
# description: One visit in source order finds an assignment expression's
# errors and the other early errors alike; in a comprehension its target's
# checks come before its value, the comprehension's clauses before its
# element. An annotation scope holding the comprehension is passed for the
# scope that binds the target; a type scope or class is an error.
from harness import *


def first(source):
    caught = assert_syntax_error(source)
    return caught.msg, caught.lineno, caught.offset


ITERABLE = "assignment expression cannot be used in a comprehension iterable expression"
CLASS = "assignment expression within a comprehension cannot be used in a class body"

# A named-expression error after another early error is not reported first.
assert_eq(first("def g():\n    [(yield) for x in y]\n    [z for z in (w := 1)]\n"),
          ("'yield' inside list comprehension", 2, 7))
assert_eq(first("def g():\n    q = 1\n    global q\n    [z for z in (w := 1)]\n"),
          ("name 'q' is assigned to before global declaration", 3, 5))
assert_eq(first("x: (yield) = 1\n[(x := 1) for x in y]\n"),
          ("yield expression cannot be used within an annotation", 1, 5))
# Clauses before the element.
assert_eq(first("[(y := 1) for y in w if (q := [p for p in (r := 2)])]\n"), (ITERABLE, 1, 44))
assert_eq(first("class C:\n    [(y := 1) for z in w if (q := 2)]\n"), (CLASS, 2, 30))
# The target's checks before the value.
assert_eq(first("[(y := [q for q in (z := 1)]) for y in w]\n"),
          ("assignment expression cannot rebind comprehension iteration variable 'y'", 1, 3))
assert_eq(first("class C:\n    [(y := 1) for y in w]\n"),
          ("assignment expression cannot rebind comprehension iteration variable 'y'", 2, 7))

# The scope that binds the target.
COMPREHENSION = "[(y := 1) for z in w]"
for source, where in ((f"def f[T: {COMPREHENSION}](): pass", "in a TypeVar bound"),
                      (f"def f[T = {COMPREHENSION}](): pass", "in a TypeVar bound"),
                      (f"def f[**P = {COMPREHENSION}](): pass", "in a TypeVar bound"),
                      (f"type A = {COMPREHENSION}", "in a type alias"),
                      (f"class C[T]({COMPREHENSION}): pass", "within the definition of a generic"),
                      (f"def f[T](a: {COMPREHENSION}): pass", "within the definition of a generic"),
                      (f"class C:\n    x: {COMPREHENSION}", "in a class body"),
                      (f"class C:\n    def f(x: {COMPREHENSION}): pass", "in a class body")):
    assert_eq(assert_syntax_error(source).msg, "assignment expression within a comprehension cannot be used " + where, source)
for source in (f"x: {COMPREHENSION}", f"def f(a: {COMPREHENSION}): pass", f"def f[T: (lambda: {COMPREHENSION})](): pass"):
    compile(source, "<spec>", "exec")

# A module annotation's comprehension binds the module's name.
namespace = {}
exec("x: [(y := 7) for z in [0]]\nr = __annotate__(1)\n", namespace)
assert_eq((namespace["r"], namespace["y"]), ({"x": [7]}, 7))
