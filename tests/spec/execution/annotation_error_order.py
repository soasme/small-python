# spec: PLS-315 8.3.1, 8.7, 16.6.1
# description: Scope analysis visits statements in source order, a compound
# statement's header before its suites and a definition's header before its
# body; a module's or class's annotation is analysed at its own statement,
# though its __annotate__ evaluates it.
from harness import *


def first(source):
    caught = assert_syntax_error(source)
    return caught.msg, caught.lineno, caught.offset


YIELD = "yield expression cannot be used within an annotation"

# A module's annotation, before a later statement's error.
assert_eq(first("x: (yield) = 1\ndef f():\n    global a\n    a: int\n"), (YIELD, 1, 5))
# A class's annotation, after an earlier statement's error and before a later one's.
assert_eq(first("class C:\n    global a\n    a: int\n    y: (yield)\n"),
          ("annotated name 'a' can't be global", 3, 5))
assert_eq(first("class C:\n    y: (yield)\n    global a\n    a: int\n"), (YIELD, 2, 9))
# A header before its suite.
assert_eq(first("def g():\n    for x in y:\n        global x\n"),
          ("name 'x' is assigned to before global declaration", 3, 9))
assert_eq(first("def g():\n    try: pass\n    except E as x:\n        global x\n"),
          ("name 'x' is assigned to before global declaration", 4, 9))
assert_eq(first("def g():\n    match v:\n        case [x]:\n            global x\n"),
          ("name 'x' is assigned to before global declaration", 4, 13))
# A declaration before a binding in its scope.
compile("def f():\n    global b\n    b = 1\n", "<spec>", "exec")
# An error at a header covers its whole statement.
caught = assert_syntax_error("try:\n   pass\nexcept TypeError as __debug__:\n   pass")
assert_eq((caught.lineno, caught.offset, caught.end_lineno, caught.end_offset), (3, 1, 4, 8))
caught = assert_syntax_error("def __debug__():\n    nonlocal q\n")
assert_eq((caught.msg, caught.lineno, caught.offset, caught.end_lineno, caught.end_offset),
          ("cannot assign to __debug__", 1, 1, 2, 15))
