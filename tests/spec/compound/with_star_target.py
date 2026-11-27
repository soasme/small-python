# spec: PLS-315 15.5
# description: a with item's starred target must star a target; otherwise
# no with item matches, and the error is "invalid syntax" at the operand's
# first token when it cannot begin a primary, else at the token after the
# longest primary it begins with.
from harness import *

for operand, at, end in [("f()", 15, 16), ("1", 13, 14), ("'s'", 15, 16), ("None", 16, 17), ("a + b", 14, 15), ("f().x()", 19, 20),
                         ("(x for x in y)", 26, 27), ("[a, f()]", 20, 21), ("(a := 1)", 20, 21), ("-a", 12, 13), ("~a", 12, 13),
                         ("not a", 12, 15), ("await a", 12, 17), ("lambda: 0", 12, 18)]:
    for form, shift in [("with a as *{}: pass", 0), ("with (b, a as *{}): pass", 4), ("with a as c, d as *{}, e: pass", 8)]:
        caught = assert_syntax_error(form.format(operand))
        assert_eq((caught.msg, caught.offset, caught.end_offset), ("invalid syntax", at + shift, end + shift), form.format(operand))
# A starred target is the compiler's error.
for operand in ["a", "a.b", "a[0]", "(a, b)", "[a, *b]"]:
    assert_eq(assert_syntax_error("with x as *%s: pass" % operand).msg, "starred assignment target must be in a list or tuple")
