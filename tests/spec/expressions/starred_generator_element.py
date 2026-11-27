# spec: PLS-315 13.2.6, 16.4
# description: a generator expression's starred element takes any
# expression, in parentheses or as a call's only argument, also in a class
# body; a list's or set's comprehension element takes a bitwise or.
from harness import *

y = [[1, 2], [], [3]]
assert_eq(list((*x or [0] for x in y)), [1, 2, 0, 3])
assert_eq(list((*x if x else [9] for x in y)), [1, 2, 9, 3])
assert_eq(list((*(lambda: x)() for x in y)), [1, 2, 3])
assert_eq(list(*x or [5] for x in y), [1, 2, 5, 3])
assert_eq(sorted(*x for x in y), [1, 2, 3])
assert_eq(sum((*x or [10] for x in y), 0), 16)
assert_eq(str(assert_raises(TypeError, list, (*a < b for a, b in [([1], [2])]))), "'bool' object is not iterable")
assert_raises(TypeError, list, (*lambda: 0 for x in y))
assert_raises(TypeError, list, (*not x for x in y))

class C:
    k = [7]
    v = list(*x for x in y)
    w = list(*x or [4] for x in y)
    g = sorted((*x for x in y), reverse=True)
assert_eq((C.v, C.w, C.g), ([1, 2, 3], [1, 2, 4, 3], [3, 2, 1]))

def f():
    k = [8]
    return list(*x or k for x in y)
assert_eq(f(), [1, 2, 8, 3])

for source in ["[*a or b for x in y]", "{*a or b for x in y}"]:
    caught = assert_syntax_error(source)
    assert_eq((caught.msg, caught.offset, caught.end_offset), ("invalid syntax", 5, 7), source)
for source, message in [("(*a := 1 for x in y)", "invalid syntax"), ("(*yield for x in y)", "Invalid star expression"),
                        ("(*a, b for x in y)", "invalid syntax"), ("f(x, *a or b for x in y)", "Generator expression must be parenthesized")]:
    assert_eq(assert_syntax_error(source).msg, message, source)
