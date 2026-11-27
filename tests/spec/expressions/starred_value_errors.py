# spec: PLS-315 13.15, 14.2
# description: a starred item alone where an expression is needed is an
# error the compiler finds, "can't use starred expression here", after
# every error of Clause 8 and in source order with the compiler's other
# errors; one in parentheses is the parser's error, "cannot use starred
# expression here"; and a starred item's operand is a bitwise_or, so a
# comparison or conditional after it is invalid syntax.
from harness import *

def error(source):
    caught = assert_syntax_error(source)
    return caught.msg, caught.lineno, caught.offset, caught.end_offset

CANT = "can't use starred expression here"
CANNOT = "cannot use starred expression here"
SCOPE = "\ndef f():\n    x = 1\n    global x\n"
for source in ["*a", "x = *a", "x: int = *a", "for x in *a: pass", "def g():\n    return *a", "def g():\n    yield *a", "f'{*a}'"]:
    assert_eq(error(source + SCOPE)[0], "name 'x' is assigned to before global declaration")
assert_eq(error("*a\nreturn"), (CANT, 1, 1, 3))
assert_eq(error("return\n*a"), ("'return' outside function", 1, 1, 7))
assert_eq(error("x = *a\nreturn"), (CANT, 1, 5, 7))
assert_eq(error("return\nx = *a"), ("'return' outside function", 1, 1, 7))
assert_eq(error("*a; b"), (CANT, 1, 1, 3))
assert_eq(error("x: int = *a"), (CANT, 1, 10, 12))
assert_eq(error("for x in *a: pass"), (CANT, 1, 10, 12))
assert_eq(error("def g():\n    return *a"), (CANT, 2, 12, 14))
assert_eq(error("def g():\n    yield *a"), (CANT, 2, 11, 13))
assert_eq(error("yield *a"), ("'yield' outside function", 1, 1, 9))
assert_eq(error("x = (yield *a)"), ("'yield' outside function", 1, 6, 14))
assert_eq(error("*a = *b"), (CANT, 1, 6, 8))
assert_eq(error("x += *a"), (CANT, 1, 6, 8))
for source, at in [("x = (*a)", 6), ("(*a)", 2), ("[(*a)]", 3), ("f((*a))", 4), ("del (*a)", 6)]:
    assert_eq(error(source), (CANNOT, 1, at, at + 2))
for source, at in [("*a < b", 4), ("x = *a < b", 8), ("*a: int = 1", 3), ("*f(): int", 5)]:
    assert_eq(error(source), ("invalid syntax", 1, at, at + 1))
assert_eq(error("*a if b else c"), ("invalid syntax", 1, 4, 6))
assert_eq(error("def g():\n    return *a b"), ("invalid syntax", 2, 15, 16))
for source in ["print(*a)", "x = *a, b", "def g():\n    return *a, b", "for x in *a, b: pass", "x = [*a]", "*a,"]:
    compile(source, "s", "exec")
