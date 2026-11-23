# spec: PLS-315 8.3.1, 28.2
# description: Early errors are found in the symbol table's visiting order:
# an assignment's, for statement's or annotated assignment's targets before
# its value, a definition's defaults before its decorators, a call's
# positional arguments before its keywords, a dictionary display's keys
# before its values, a comprehension clause's target before its iterable,
# and a conditional expression's test first. Locals are still numbered in
# evaluation order.
from harness import *

A, B = "[(yield) for a in b]", "[(yield) for c in d]"
for template, line, offset in (("x[%s] = %s", 2, 9), ("for x[%s] in %s: pass", 2, 13), ("x[%s]: int = %s", 2, 9),
                               ("{1: %s, %s: 2}", 2, 33), ("{**%s, %s: 1}", 2, 32), ("f(k=%s, *%s)", 2, 34),
                               ("@%s\ndef f(a=%s): pass", 3, 15), ("[x for x in y for z[%s] in %s]", 2, 27),
                               ("%s if 1 else %s", 2, 7), ("1 if %s else %s", 2, 12)):
    body = template % (A, B)
    caught = assert_syntax_error("def g():\n" + "".join("    " + text + "\n" for text in body.splitlines()))
    assert_eq((caught.msg, caught.lineno, caught.offset), ("'yield' inside list comprehension", line, offset), template)


def numbered():
    x = (y := 1)
    for i in (w := [2]): pass
    p: int = (q := 3)
    m = (n := 1) if (o := 2) else (k := 3)
    def inner(a=(z := 1)): pass
    class K((b := object)): pass


assert_eq(numbered.__code__.co_varnames, ("y", "x", "w", "i", "q", "p", "o", "n", "k", "m", "z", "inner", "b", "K"))
