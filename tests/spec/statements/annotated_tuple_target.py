# spec: PLS-315 14.4
# description: an annotated assignment whose target is a tuple is an error
# located at the tuple when it is parenthesized, else at its first item,
# that item's own parentheses excluded.
from harness import *

TUPLE = "only single target (not tuple) can be annotated"
for source, at, end in [("a, b: int = 1", 1, 2), ("(a, b): int = 1", 1, 7), ("a, (b, c): int = 1", 1, 2), ("(a, (b, c)): int = 1", 1, 12),
                        ("a, b: int", 1, 2), ("a, [b]: int", 1, 2), ("(a), b: int", 2, 3), ("a.b, c: int", 1, 4), ("f(), b: int", 1, 4),
                        ("(a, b), c: int", 1, 7), ("*a, b: int", 1, 3), ("a, *b: int", 1, 2), ("a, b, c: int", 1, 2)]:
    caught = assert_syntax_error(source)
    assert_eq((caught.msg, caught.offset, caught.end_offset), (TUPLE, at, end), source)
caught = assert_syntax_error("[a, b]: int")
assert_eq((caught.msg, caught.offset, caught.end_offset), ("only single target (not list) can be annotated", 1, 7))
