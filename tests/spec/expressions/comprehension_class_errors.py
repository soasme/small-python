# spec: PLS-315 13.2.6
# description: in a class body read from a file, a display whose first item
# starts a comprehension's own program and is then followed by more items
# reports the comprehension target error, as at module level, and a class
# body's comprehensions still evaluate.
from harness import *

def error(name):
    try:
        __import__(name)
    except SyntaxError as e:
        return e.msg, e.lineno, e.offset, e.end_lineno, e.end_offset
    fail(f"{name} imported")

target = "did you forget parentheses around the comprehension target?"
assert_eq(error("class_pair"), (target, 2, 6, 2, 10))
assert_eq(error("class_comma"), (target, 2, 6, 2, 8))
import class_ok
assert_eq((class_ok.C.y, class_ok.C.z, class_ok.C.w), ([2], {1: 2}, [1]))
