# spec: PLS-315 14.13, 8.3.1
# description: a future statement's errors are found before every error of
# Clause 8: a feature that is not defined, and a future statement after the
# module's first other statement on that statement's line. A misplaced
# future statement on a later line is an error of Clause 8, found in source
# order with them, after its names; the features it names are not checked.
from harness import *

def error(source):
    caught = assert_syntax_error(source)
    return caught.msg, caught.lineno, caught.offset, caught.end_offset

SCOPE = "def f():\n    x = 1\n    global x\n"
GLOBAL = "name 'x' is assigned to before global declaration"
MISPLACED = "from __future__ imports must occur at the beginning of the file"
# Before Clause 8's errors, wherever they are.
assert_eq(error("from __future__ import nope\n" + SCOPE), ("future feature nope is not defined", 1, 24, 28))
assert_eq(error("from __future__ import braces\n" + SCOPE), ("not a chance", 1, 24, 30))
assert_eq(error("from __future__ import annotations\nfrom __future__ import *\n" + SCOPE), ("future feature * is not defined", 2, 24, 25))
assert_eq(error("x = 1; from __future__ import nope\n" + SCOPE), (MISPLACED, 1, 8, 35))
assert_eq(error("from __future__ import annotations\nx = 1; y = 2; from __future__ import nope\n" + SCOPE), (MISPLACED, 2, 15, 42))
assert_eq(error('"doc"; from __future__ import nope\n' + SCOPE), ("future feature nope is not defined", 1, 31, 35))
assert_eq(error("from __future__ import nope\nfrom __future__ import braces"), ("future feature nope is not defined", 1, 24, 28))
assert_eq(error("from __future__ import nope\nreturn 1"), ("future feature nope is not defined", 1, 24, 28))
# On a later line, in source order with Clause 8's errors.
assert_eq(error("x = 1\nfrom __future__ import annotations\n" + SCOPE), (MISPLACED, 2, 1, 35))
assert_eq(error("x = 1\nfrom __future__ import nope\n" + SCOPE), (MISPLACED, 2, 1, 28))
assert_eq(error(SCOPE + "from __future__ import annotations\n"), (GLOBAL, 3, 5, 13))
assert_eq(error(SCOPE + "from __future__ import nope\n"), (GLOBAL, 3, 5, 13))
assert_eq(error('"doc"\n"two"\nfrom __future__ import annotations\n' + SCOPE), (MISPLACED, 3, 1, 35))
assert_eq(error("if 1:\n    from __future__ import annotations\n" + SCOPE), (MISPLACED, 2, 5, 39))
assert_eq(error("x = 1\nfrom __future__ import *\n" + SCOPE), (MISPLACED, 2, 1, 25))
assert_eq(error("def f():\n    from __future__ import *"), ("import * only allowed at module level", 2, 28, 29))
assert_eq(error("return 1\nfrom __future__ import annotations"), (MISPLACED, 2, 1, 35))
# Clause 8's errors still come before the compiler's.
assert_eq(error("x = 1\nfrom __future__ import annotations\nreturn 1"), (MISPLACED, 2, 1, 35))
