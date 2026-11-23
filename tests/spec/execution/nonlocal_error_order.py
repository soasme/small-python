# spec: PLS-315 8.4, 14.9, 18.2.1
# description: Of several nonlocal errors, the first met visiting scopes from
# the root downward is raised: a scope's own before those within it, sibling
# scopes in source order; an asynchronous generator's valued return is
# reported only when no scope has such an error.
from harness import *


def first(source):
    caught = assert_syntax_error(source)
    return caught.msg, caught.lineno, caught.offset


# Sibling scopes in source order.
assert_eq(first("def f():\n    nonlocal a\ndef g():\n    nonlocal b\n"),
          ("no binding for nonlocal 'a' found", 2, 5))
# A scope before the scopes within it, wherever they are in the source.
assert_eq(first("def f():\n    def h():\n        nonlocal a\n    nonlocal b\n"),
          ("no binding for nonlocal 'b' found", 4, 5))
assert_eq(first("def f():\n    nonlocal b\n    def h():\n        nonlocal a\n"),
          ("no binding for nonlocal 'b' found", 2, 5))
# A method's scope is within its class's.
assert_eq(first("class C:\n    def m(self):\n        nonlocal q\ndef g():\n    nonlocal r\n"),
          ("no binding for nonlocal 'q' found", 3, 9))
# The module's own error comes first.
assert_eq(first("def f():\n    nonlocal a\nnonlocal top\n"),
          ("nonlocal declaration not allowed at module level", 3, 1))

# An asynchronous generator's valued return: the first in source order,
# at the return statement, and only after every scope's nonlocal names.
assert_eq(first("async def f():\n    yield 1\n    return 2\nasync def g():\n    yield 1\n    return 3\n"),
          ("'return' with value in async generator", 3, 5))
assert_eq(first("async def f():\n    yield 1\n    return 2\ndef g():\n    nonlocal z\n"),
          ("no binding for nonlocal 'z' found", 5, 5))
assert_eq(first("def g():\n    nonlocal z\nasync def f():\n    yield 1\n    return 2\n"),
          ("no binding for nonlocal 'z' found", 2, 5))
caught = assert_syntax_error("async def f():\n    yield 1\n    if x: return (2 +\n 3)\n")
assert_eq((caught.lineno, caught.offset, caught.end_lineno, caught.end_offset), (3, 11, 4, 4))
