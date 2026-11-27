# spec: PLS-315 15.3, 13.2.6
# description: a for target that is not star_targets before 'in' is read
# again as star_expressions and is the error of its invalid part, the left
# operand of a comparison begun by 'in' searched; a comprehension's for
# clause first reports bitwise-or operands that 'in' does not follow.
from harness import *

LAMBDA, CONDITIONAL, EXPRESSION = "cannot assign to lambda", "cannot assign to conditional expression", "cannot assign to expression"
for target, message, at, end in [("lambda: 0", LAMBDA, 5, 19), ("a if b else c", CONDITIONAL, 5, 23), ("not a", EXPRESSION, 5, 15),
                                 ("a or b", EXPRESSION, 5, 16), ("a, lambda: 0", LAMBDA, 8, 22), ("lambda: 0, a", LAMBDA, 5, 14),
                                 ("f() if a else b", CONDITIONAL, 5, 25), ("-a if b else c", CONDITIONAL, 5, 24), ("a or b, c", EXPRESSION, 5, 11),
                                 ("f()", "cannot assign to function call", 5, 8), ("a < b", "invalid syntax", 7, 8), ("a b", "invalid syntax", 7, 8)]:
    for form, shift in [("for {} in x: pass", 0), ("async def g():\n    async for {} in x: pass", 10)]:
        caught = assert_syntax_error(form.format(target))
        assert_eq((caught.msg, caught.offset, caught.end_offset), (message, at + shift, end + shift), form.format(target))

IN = "'in' expected after for-loop variables"
for target, message, at, end in [("lambda: 0", LAMBDA, 8, 22), ("not a", EXPRESSION, 8, 18), ("lambda: 0, a", LAMBDA, 8, 17),
                                 ("a, lambda: 0", IN, 11, 17), ("a, not b", IN, 11, 14), ("a if b else c", IN, 10, 12),
                                 ("*a if b else c", "invalid syntax", 11, 13), ("a, *b if c else d", IN, 14, 16), ("f()", "cannot assign to function call", 8, 11)]:
    for form, shift in [("[0 for {} in x]", 0), ("(0 for {} in x)", 0), ("{{0: 1 for {} in x}}", 3), ("[0 for a in b for {} in x]", 11)]:
        caught = assert_syntax_error(form.format(target))
        assert_eq((caught.msg, caught.offset, caught.end_offset), (message, at + shift, end + shift), form.format(target))

# A for target's own parse error keeps the parser's location.
for target, message, at, end in [("((*a))", "cannot use starred expression here", 7, 9), ("[*a, **a]", "cannot use dict unpacking here", 10, 12),
                                 ("[*a, *a if b else c]", "invalid starred expression. Did you forget to wrap the conditional expression in parentheses?", 10, 24)]:
    caught = assert_syntax_error("for %s in x: pass" % target)
    assert_eq((caught.msg, caught.offset, caught.end_offset), (message, at, end), target)
