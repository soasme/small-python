# spec: PLS-315 13.15
# description: a parenthesized starred item that no comma follows takes any
# expression, "cannot use starred expression here" over it; an operand that
# fails at its first token is "Invalid star expression"; an item that a
# comma follows takes a bitwise or.
from harness import *

HERE = "cannot use starred expression here"
for source, message, at, end in [("(*lambda: 0)", HERE, 2, 12), ("x = (*lambda: 0)", HERE, 6, 16), ("f((*lambda: 0))", HERE, 4, 14),
                                 ("(*not a)", HERE, 2, 8), ("(*a or b)", HERE, 2, 9), ("(*a)", HERE, 2, 4), ("(*await a)", HERE, 2, 10),
                                 ("for x in (*lambda: 0): pass", HERE, 11, 21), ("(*yield)", "Invalid star expression", 3, 8),
                                 ("(*a := 1)", "invalid syntax", 5, 7), ("(*a, *lambda: 0)", "invalid syntax", 7, 13), ("[*lambda: 0]", "invalid syntax", 3, 9),
                                 ("(*f(, b)", "invalid syntax", 5, 6), ("(*a b)", "invalid syntax. Perhaps you forgot a comma?", 3, 6),
                                 ("(*a if b else c)", "invalid starred expression. Did you forget to wrap the conditional expression in parentheses?", 2, 16)]:
    caught = assert_syntax_error(source)
    assert_eq((caught.msg, caught.offset, caught.end_offset), (message, at, end), source)
