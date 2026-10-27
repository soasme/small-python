# spec: reference/toplevel_components.html
# description: Invalid programs raise SyntaxError with the right message and position.
from harness import *

src = """
def valid_func():
    pass

yield 2
"""

with assert_raises(SyntaxError) as ae:
    compile(src, 'test.py', 'exec')
assert ae.exception.lineno == 5

src = """
if True:
pass
"""

with assert_raises(IndentationError):
    compile(src, '', 'exec')

src = """
if True:
  pass
    pass
"""

with assert_raises(IndentationError):
    compile(src, '', 'exec')

src = """
if True:
    pass
  pass
"""

with assert_raises(IndentationError):
    compile(src, '', 'exec')

src = """
if True:
    pass
\tpass
"""

with assert_raises(TabError):
    compile(src, '', 'exec')

with assert_raises(SyntaxError):
    compile('0xX', 'test.py', 'exec')


src = """
"aaaa" \a
"bbbb"
"""

with assert_raises(SyntaxError):
    compile(src, 'test.py', 'exec')

src = """
from __future__ import not_a_real_future_feature
"""

with assert_raises(SyntaxError):
    compile(src, 'test.py', 'exec')

src = """
a = 1
from __future__ import print_function
"""

with assert_raises(SyntaxError):
    compile(src, 'test.py', 'exec')

src = """
from __future__ import print_function
"""
compile(src, 'test.py', 'exec')


# CPython reports the unparenthesized `except ... as` error with a range that starts at the
# first exception type and stops just before the `:` closing the clause. `end_offset` is an
# exclusive 1-based *character* column, so that end lands on the column the `:` sits on.
#
# The cases below pin the parts that are easy to get wrong: the column counts characters
# rather than UTF-8 bytes, and an explicit line join may sit anywhere between the exception
# types and the `:`. Values verified against CPython 3.14.
except_as_ranges = [
    # (clause, (lineno, offset), (end_lineno, end_offset))
    ("except A, B as e:", (3, 8), (3, 17)),
    ("except A, B as e :", (3, 8), (3, 18)),
    ("except A, B as e   :", (3, 8), (3, 20)),
    ("except A, B as e\t:", (3, 8), (3, 18)),
    ("except A, B, C as blech:", (3, 8), (3, 24)),
    ("except* A, B, C as e:", (3, 9), (3, 21)),
    # A non-ASCII name must not push the column right by its extra UTF-8 bytes.
    ("except Ä, B as e:", (3, 8), (3, 17)),
    ("except 사과, B as e:", (3, 8), (3, 18)),
    ("except A, B as 오:", (3, 8), (3, 17)),
    # An explicit line join may precede or follow `as`, or close the clause on its own line.
    ("except A, B as exc\\\n    :", (3, 8), (4, 5)),
    ("except A, B \\\nas exc:", (3, 8), (4, 7)),
    ("except A, \\\nB as exc:", (3, 8), (4, 9)),
    ("except A, B as \\\nexc:", (3, 8), (4, 4)),
]

for clause, start, end in except_as_ranges:
    src = "try:\n    pass\n%s\n    pass\n" % clause
    with assert_raises(SyntaxError) as ae:
        compile(src, "test.py", "exec")
    exc = ae.exception
    assert exc.msg == "multiple exception types must be parenthesized when using 'as'", (
        clause,
        exc.msg,
    )
    assert (exc.lineno, exc.offset) == start, (clause, (exc.lineno, exc.offset), start)
    assert (exc.end_lineno, exc.end_offset) == end, (
        clause,
        (exc.end_lineno, exc.end_offset),
        end,
    )
# Walrus targets: the first expression of a statement names the bad target,
# a call argument does not.
for source, message in (("x[1] := 2", "cannot use assignment expressions with subscript"),
                        ("(x) := 1", "cannot use assignment expressions with name"),
                        ("f() := 2", "cannot use assignment expressions with function call"),
                        ("a, b := 2", "invalid syntax"),
                        ("print(x.y := 1)", "invalid syntax"),
                        ("[x[1] := 2]", "cannot use assignment expressions with subscript"),
                        ("match 1:\n  case *x: pass", "invalid syntax")):
    assert_eq(assert_syntax_error(source).msg, message)
# A bare except that is not last is a compiler error: parse errors and symbol
# table errors come first.
error = assert_syntax_error("try: pass\nexcept: pass\nexcept ValueError: pass")
assert_eq((error.msg, error.lineno), ("default 'except:' must be last", 2))
assert_eq(assert_syntax_error("try: pass\nexcept: pass\nexcept E: pass\ndef f():\n  nonlocal x").msg,
          "no binding for nonlocal 'x' found")
error = assert_syntax_error("try: pass\nexcept* E: pass\nexcept E: pass")
assert_eq((error.lineno, error.offset), (3, 1))
# Indentation errors carry the tokenizer's columns.
error = assert_syntax_error("x\n    y\n", exception=IndentationError)
assert_eq((error.msg, error.offset, error.end_offset), ("unexpected indent", 4, -1))
error = assert_syntax_error("if 1:\n    x\n  y = 1\n", exception=IndentationError)
assert_eq((error.lineno, error.offset, error.end_offset), (3, 8, -1))
error = assert_syntax_error("a) + 1\n")
assert_eq((error.text, error.offset, error.end_offset), ("a) + 1", 2, 2))
# Call argument ordering errors.
for source, message, offset, end in (
        ("f(**k, a)", "positional argument follows keyword argument unpacking", 9, 10),
        ("f(a=1, b)", "positional argument follows keyword argument", 9, 10),
        ("f(**k, *a)", "iterable argument unpacking follows keyword argument unpacking", 6, 10),
        ("f(**k, *a, *b, c)", "iterable argument unpacking follows keyword argument unpacking", 6, 16),
        ("f(*a=1)", "cannot assign to iterable argument unpacking", 3, 7),
        ("f(a=1, b for b in c)", "Generator expression must be parenthesized", 8, 20)):
    error = assert_syntax_error(source)
    assert_eq((error.msg, error.offset, error.end_offset), (message, offset, end))
# Compile-time errors cover the source of the node that causes them.
for source, message, position in (
        ("__debug__ = 1", "cannot assign to __debug__", (1, 1, 1, 10)),
        ("x.__debug__ = 1", "cannot assign to __debug__", (1, 1, 1, 12)),
        ("f(__debug__=1)", "cannot assign to __debug__", (1, 3, 1, 14)),
        ("def __debug__(): pass", "cannot assign to __debug__", (1, 1, 1, 22)),
        ("import a as __debug__", "cannot assign to __debug__", (1, 8, 1, 22)),
        ("def f(__debug__): pass", "cannot assign to __debug__", (1, 7, 1, 16)),
        ("def f(x):\n  global x", "name 'x' is parameter and global", (2, 3, 2, 11)),
        ("def f():\n  global x\n  nonlocal x", "name 'x' is nonlocal and global", (2, 3, 2, 11)),
        ("return 1", "'return' outside function", (1, 1, 1, 9)),
        ("x = yield 2", "'yield' outside function", (1, 5, 1, 12)),
        ("await x", "'await' outside function", (1, 1, 1, 8)),
        ("f(a=1, a=2)", "keyword argument repeated: a", (1, 8, 1, 11)),
        ("[x async for x in y]", "asynchronous comprehension outside of an asynchronous function", (1, 1, 1, 21)),
        ("async def f(): yield from x", "'yield from' inside async function", (1, 16, 1, 28)),
        ("[i := 0 for i in x]", "assignment expression cannot rebind comprehension iteration variable 'i'", (1, 2, 1, 3)),
        ("[x for x in (y := 1)]", "assignment expression cannot be used in a comprehension iterable expression", (1, 14, 1, 20))):
    error = assert_syntax_error(source)
    assert_eq((error.msg, (error.lineno, error.offset, error.end_lineno, error.end_offset)), (message, position))
# Parser errors that name a construct cover it.
for source, message, position in (
        ("(): int", "only single target (not tuple) can be annotated", (1, 1, 1, 3)),
        ("-x: int = 1", "illegal target for annotation", (1, 1, 1, 3)),
        ("a, *b, c, *d, e = x", "multiple starred expressions in assignment", (1, 1, 1, 16)),
        ("*a = x", "starred assignment target must be in a list or tuple", (1, 1, 1, 3)),
        ("x = *a", "can't use starred expression here", (1, 5, 1, 7)),
        ("[**x for x in y]", "cannot use dict unpacking in list comprehension", (1, 2, 1, 5)),
        ("(**a)", "cannot use dict unpacking here", (1, 2, 1, 4)),
        ("[*x if x else y for x in z]", "invalid starred expression. Did you forget to wrap the conditional expression in parentheses?", (1, 2, 1, 16)),
        ("A[*(1:2)]", "Invalid star expression", (1, 6, 1, 7)),
        ("f((x)=2)", "expression cannot contain assignment, perhaps you meant \"==\"?", (1, 4, 1, 7)),
        ("dict(a = i for i in y)", "invalid syntax. Maybe you meant '==' or ':=' instead of '='?", (1, 6, 1, 9)),
        ("type A = (x := 3)", "named expression cannot be used within a type alias", (1, 11, 1, 17)),
        ("try:\n   x = 34\n", "expected 'except' or 'finally' block", (2, 10, 2, -1))):
    error = assert_syntax_error(source)
    assert_eq((error.msg, (error.lineno, error.offset, error.end_lineno, error.end_offset)), (message, position))
error = assert_syntax_error("match x:\n    case []:\npass\n", exception=IndentationError)
assert_eq((error.lineno, error.offset, error.end_offset), (3, 0, -1))
error = assert_syntax_error("class C:\n", exception=IndentationError)
assert_eq((error.lineno, error.offset, error.end_offset), (1, 9, -1))
# Ranges of the remaining invalid_* rules.
for source, message, position in (
        ("f(True=1)", "cannot assign to True", (1, 3, 1, 8)),
        ("f(a=)", "expected argument value expression", (1, 3, 1, 5)),
        ("if x = 3:\n   pass", "invalid syntax. Maybe you meant '==' or ':=' instead of '='?", (1, 4, 1, 9)),
        ("def f(x, (y, z), w):\n   pass", "Function parameters cannot be parenthesized", (1, 10, 1, 16)),
        ("{1: *12+1}", "cannot use a starred expression in a dictionary value", (1, 5, 1, 10)),
        ("import a from b as bar", "Did you mean to use 'from ... import ...' instead?", (1, 1, 1, 18)),
        ("import\n", "Expected one or more names after 'import'", (1, 7, 1, 7)),
        ("type A[] = int", "Type parameter list cannot be empty", (1, 8, 1, 10)),
        ("class A[]: ...", "Type parameter list cannot be empty", (1, 9, 1, 9)),
        ("type A = (yield from [])", "yield expression cannot be used within a type alias", (1, 11, 1, 24)),
        ("class A[T]((await 3)): ...", "await expression cannot be used within the definition of a generic", (1, 13, 1, 20)),
        ("assert 'a' = a", "cannot assign to literal here. Maybe you meant '==' instead of '='?", (1, 8, 1, 15)),
        ("match ...:\n  case Foo(y=1, x=2, y=3):\n    ...", "attribute name repeated in class pattern: y", (2, 24, 2, 25)),
        ("match x:\n case y as __debug__: pass", "cannot assign to __debug__", (2, 7, 2, 21)),
        ("try:\n   pass\nexcept TypeError as __debug__:\n   pass", "cannot assign to __debug__", (3, 1, 4, 8)),
        ("def f(a: int, __debug__: int = 3): pass", "cannot assign to __debug__", (1, 15, 1, 29))):
    error = assert_syntax_error(source)
    assert_eq((error.msg, (error.lineno, error.offset, error.end_lineno, error.end_offset)), (message, position))
