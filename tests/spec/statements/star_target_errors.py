# spec: PLS-315 14.2, 8.3.1
# description: a starred target alone, two starred targets in one list and
# too many targets before a starred one are errors the compiler finds:
# after every error of Clause 8 and every target that cannot be assigned,
# in source order with the compiler's other errors, an assignment's value
# and a for statement's iterable before its targets.
from harness import *

def error(source):
    caught = assert_syntax_error(source)
    return caught.msg, caught.lineno, caught.offset, caught.end_offset

ALONE = "starred assignment target must be in a list or tuple"
TWO = "multiple starred expressions in assignment"
SCOPE = "\ndef f():\n    x = 1\n    global x\n"
GLOBAL = "name 'x' is assigned to before global declaration"
# Clause 8's errors come first.
for source in ["*a = 1", "(*a, *b) = 1", "for *a in x: pass", "[0 for *a in x]", "with x as *a: pass"]:
    assert_eq(error(source + SCOPE)[0], GLOBAL)
# A target that cannot be assigned, a parser's error, comes first.
assert_eq(error("*f() = 1"), ("cannot assign to function call", 1, 2, 5))
assert_eq(error("[*a, *f()] = 1"), ("cannot assign to function call", 1, 7, 10))
assert_eq(error("(*a, *1) = 1"), ("cannot assign to literal", 1, 7, 8))
assert_eq(error("(*a, *b) = 1\n*f() = 1"), ("cannot assign to function call", 2, 2, 5))
assert_eq(error("for [*a, *'s'] in x: pass"), ("cannot assign to literal", 1, 11, 14))
assert_eq(error("[0 for *f() in x]"), ("cannot assign to function call", 1, 9, 12))
assert_eq(error("del *a"), ("cannot delete starred", 1, 5, 7))
# In source order with the compiler's other errors.
assert_eq(error("return\n*a = 1"), ("'return' outside function", 1, 1, 7))
assert_eq(error("*a = 1\nreturn"), (ALONE, 1, 1, 3))
assert_eq(error("*a, = 1; (*b, *c) = 1"), (TWO, 1, 10, 18))
assert_eq(error("a, *b, c, *d = 1"), (TWO, 1, 1, 13))
assert_eq(error("with x as *a, (yield) as b: pass"), (ALONE, 1, 11, 13))
assert_eq(error("for x in y:\n    *a = 1\n    continue"), (ALONE, 2, 5, 7))
# The value or iterable first, then the targets in order.
assert_eq(error("*a = yield"), ("'yield' outside function", 1, 6, 11))
assert_eq(error("*a = b = (yield)"), ("'yield' outside function", 1, 11, 16))
assert_eq(error("*a = (*b, *c) = 1"), (ALONE, 1, 1, 3))
assert_eq(error("(*a, *b) = *c = 1"), (TWO, 1, 1, 9))
assert_eq(error("for *a in (yield): pass"), ("'yield' outside function", 1, 12, 17))
assert_eq(error("for *a in x: yield"), (ALONE, 1, 5, 7))
assert_eq(error("with (yield) as *a: pass"), ("'yield' outside function", 1, 7, 12))
# A comprehension's yield is an error of Clause 8.
assert_eq(error("[0 for *a in y if (yield)]"), ("'yield' inside list comprehension", 1, 20, 25))
assert_eq(error("[0 for (*a, *b) in y for c in (yield)]"), ("'yield' inside list comprehension", 1, 32, 37))
# Located at the starred target, or the list holding two.
assert_eq(error("[a, *(b, *c, *d)] = 1"), (TWO, 1, 6, 17))
assert_eq(error("async def g():\n    async with x as *a: pass"), (ALONE, 2, 21, 23))
names = ", ".join("x%d" % i for i in range(300))
assert_eq(error(names + ", *a = c")[:3], ("too many expressions in star-unpacking assignment", 1, 1))
