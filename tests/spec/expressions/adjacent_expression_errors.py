# spec: PLS-315 13.13
# description: two adjacent expressions inside brackets are a missing comma
# over both, the second as much as parses, None, True and False counting
# as expressions before a string; a print followed by expressions misses
# its parentheses over as much of them as parses.
from harness import *

COMMA = "invalid syntax. Perhaps you forgot a comma?"
PRINT = "Missing parentheses in call to 'print'. Did you mean print(...)?"
for source, message, at, end in [("f(Strict()value.)", COMMA, 3, 16), ("f(x()send., 1)", COMMA, 3, 10), ("[0, 4 5.]", COMMA, 5, 9),
                                 ("f(a b.c.)", COMMA, 3, 8), ("f(b'x'endswith.(1))", COMMA, 3, 15), ("f(None 'm')", COMMA, 3, 11),
                                 ("f(True 'm')", COMMA, 3, 11), ("f(a 'm')", "invalid syntax", 5, 8),
                                 ("print 'a'(.x)", PRINT, 1, 10), ("print 'a' +", PRINT, 1, 10)]:
    caught = assert_syntax_error(source)
    assert_eq((caught.msg, caught.offset, caught.end_offset), (message, at, end), source)
