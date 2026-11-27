# spec: PLS-315 14.4
# description: an annotated assignment's target errors need an annotation
# after the colon; without one the statement is invalid syntax, after the
# colon for a name and at the colon for any other target. A yield is no
# annotation.
from harness import *

for source, message, at, end in [("f():", "invalid syntax", 4, 5), ("a, b:", "invalid syntax", 5, 6), ("[a]:", "invalid syntax", 4, 5),
                                 ("(a, b):", "invalid syntax", 7, 8), ("1:", "invalid syntax", 2, 3), ("a:", "invalid syntax", 3, 4),
                                 ("classA (B):", "invalid syntax", 11, 12),
                                 ("f(): int", "illegal target for annotation", 1, 4), ("a, b: int", "only single target (not tuple) can be annotated", 1, 2),
                                 ("[a]: int", "only single target (not list) can be annotated", 1, 4), ("f(): yield", "invalid syntax", 4, 5),
                                 ("f(): lambda: 0", "illegal target for annotation", 1, 4)]:
    caught = assert_syntax_error(source)
    assert_eq((caught.msg, caught.offset, caught.end_offset), (message, at, end), source)
