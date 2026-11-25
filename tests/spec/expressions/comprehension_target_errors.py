# spec: PLS-315 13.2.6
# description: an unparenthesized tuple as a list or set comprehension's
# element, its items followed by a for clause (with or without a trailing
# comma), is "did you forget parentheses around the comprehension
# target?" over the items, once its first for clause parses: an error in
# that clause's target comes first, and an iterable that does not parse
# leaves invalid syntax at the for. In parentheses or a dictionary display
# the for is invalid syntax; a dictionary's leading ** is "cannot use dict
# unpacking here". A ** item is "cannot use dict unpacking in list
# comprehension" (or "... in generator expression") only as the sole
# element of a for clause that parses. A key in a set display is invalid
# syntax at its ':'.
from harness import *

def error(source):
    e = assert_syntax_error(source)
    return e.msg, e.lineno, e.offset, e.end_lineno, e.end_offset

target = "did you forget parentheses around the comprehension target?"
here = "cannot use dict unpacking here"
cases = {
    "[a, b for a in c]": (target, 1, 2, 1, 6),
    "{a, b for a in c}": (target, 1, 2, 1, 6),
    "[a, for a in c]": (target, 1, 2, 1, 4),
    "{a, b, for a in c}": (target, 1, 2, 1, 6),
    "[a, b, async for x in y]": (target, 1, 2, 1, 6),
    "[*a, for a in c]": (target, 1, 2, 1, 5),
    "[a,\n b for a in c]": (target, 1, 2, 2, 3),
    "[a, b for x in y if]": (target, 1, 2, 1, 6),
    "[a, b for x in y, z]": (target, 1, 2, 1, 6),
    "[a, b for x in]": ("invalid syntax", 1, 7, 1, 10),
    "[a, b for x in lambda: 1]": ("invalid syntax", 1, 7, 1, 10),
    "[a, b async x]": ("invalid syntax", 1, 7, 1, 12),
    "[a, b for]": ("invalid syntax", 1, 7, 1, 10),
    "[a, b for 1 in y]": ("cannot assign to literal", 1, 11, 1, 12),
    "[a, for x]": ("'in' expected after for-loop variables", 1, 10, 1, 11),
    "(a, b for a in c)": ("invalid syntax", 1, 7, 1, 10),
    "(a, b async for a in c)": ("invalid syntax", 1, 7, 1, 12),
    "(a, for a in c)": ("invalid syntax", 1, 5, 1, 8),
    "(a, b for 1 in y)": ("invalid syntax", 1, 7, 1, 10),
    "(a, b\n for a in c)": ("invalid syntax", 2, 2, 2, 5),
    "{a: 1, b: 2 for a in c}": ("invalid syntax", 1, 13, 1, 16),
    "{a: 1, for a in c}": ("invalid syntax", 1, 8, 1, 11),
    "{a: 1, **b for a in c}": ("invalid syntax", 1, 12, 1, 15),
    "{**a, b: 1 for a in c}": (here, 1, 2, 1, 4),
    "{**a, for}": (here, 1, 2, 1, 4),
    "{ **a , b: 1 for a in c}": (here, 1, 3, 1, 5),
    "[x, **a for a in c]": (here, 1, 5, 1, 7),
    "(x, **a for a in c)": (here, 1, 5, 1, 7),
    "[**a for]": (here, 1, 2, 1, 4),
    "[**a for x in y]": ("cannot use dict unpacking in list comprehension", 1, 2, 1, 5),
    "(**a for x in y)": ("cannot use dict unpacking in generator expression", 1, 2, 1, 5),
    "[**a for 1 in y]": ("cannot assign to literal", 1, 10, 1, 11),
    "{a, b: 1}": ("invalid syntax", 1, 6, 1, 7),
    "{a, b: 1 for a in c}": ("invalid syntax", 1, 6, 1, 7),
}
assert_eq({source: error(source) for source in cases}, cases)
# A comprehension's own element still parses.
assert_eq([(a, b) for a in "x" for b in "y"], [("x", "y")])
