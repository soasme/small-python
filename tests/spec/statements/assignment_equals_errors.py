# spec: PLS-315 14.2
# description: an assignment whose target cannot be assigned is first read
# as a name or bitwise-or operand that '=' and an operand not followed by
# '=' or ':=' follow: "Maybe you meant '==' ...", unless the statement
# begins with a list, tuple or generator expression (parentheses around one
# bracketed group begin none of them); a generator target included.
from harness import *

MEANT = "invalid syntax. Maybe you meant '==' or ':=' instead of '='?"
def here(what): return "cannot assign to %s here. Maybe you meant '==' instead of '='?" % what
for source, message, at, end in [("a = a, ((x for x in y), c) = 1", MEANT, 1, 6), ("a = (x for x in y), c = 1", MEANT, 1, 19),
                                 ("a = a, f() = 1", MEANT, 1, 6), ("(((x for x in y))) = 1", here("generator expression"), 3, 17),
                                 ("((x for x in y)) = 1", here("generator expression"), 2, 16), ("((a, f())) = 1", here("tuple"), 2, 10),
                                 ("([a, f()]) = 1", here("list"), 2, 10), ("((f())) = 1", here("function call"), 3, 6), ("f() = 1", here("function call"), 1, 4),
                                 ("(x for x in y) = 1", "cannot assign to generator expression", 1, 15), ("[(x for x in y)] = 1", "cannot assign to generator expression", 2, 16),
                                 ("(a, f()) = 1", "cannot assign to function call", 5, 8), ("a = b = f() = 1", "cannot assign to function call", 9, 12)]:
    caught = assert_syntax_error(source)
    assert_eq((caught.msg, caught.offset, caught.end_offset), (message, at, end), source)
