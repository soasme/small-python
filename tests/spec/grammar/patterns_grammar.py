# spec: PLS-315 A.9, 15.6.2
# description: The pattern grammar of Annex A: literal, capture, value, group, sequence, mapping, and class patterns.
from harness import *

def accepts(pattern):
    assert_compiles(f"match s:\n    case {pattern}:\n        pass\n")

def rejects(pattern):
    assert_syntax_error(f"match s:\n    case {pattern}:\n        pass\n")

for pattern in (
        # literal_pattern
        "1", "-1", "+1", "1.5", "-1.5", "1j", "-1j", "1 + 2j", "-1 - 2j", "1.5 + 2.5j", "'a'", "'a' 'b'",
        "b'a'", "None", "True", "False",
        # capture, wildcard, value, group
        "x", "_", "a.b", "a.b.c", "(x)", "((1))",
        # sequences
        "[]", "()", "[x]", "(x,)", "x,", "x, y", "[x, *y]", "(*x, y)", "*_, y", "[1, [2, (3, *_)]]",
        # or and as
        "1 | 2", "x as y", "(1 | 2) as y", "[1 | 2 as y, *z]", "(1 as x) | (2 as x)",
        # mappings
        "{}", "{'a': x}", "{'a': x,}", "{1: _, a.b: [y], None: z}", "{'a': 1, **rest}", "{'a': 1, **rest,}",
        "{b'k': 1, -1: 2, 1+2j: 3, True: 4}",
        # classes
        "C()", "C(x)", "C(x,)", "C(x, y=1)", "a.b.C(y=[1], z={})", "C(y=1,)", "int(x) | str(x)"):
    accepts(pattern)

for pattern in (
        "1 + 2", "1 - 1", "-1 + 2 + 3j", "1j + 2", "1 + -2j", "a + 1", "2 * 3",
        "not x", "a[0]", "a.b as c.d", "x as _", "x as 1", "_ as y()",
        "*x", "*1", "[*x, *y]", "(*_, *_)", "**x", "{**rest, 'a': 1}", "{**_}", "{x: 1}",
        "{*x}", "{'a'}", "C(y=1, x)", "C(**k)", "C(*a)", "C(a.b=1)",
        "f'a'", "f'{x}'", "t'a'", "1 if x else 2", "(x := 1)", "lambda: 1", "x | ", "| x", "...", "[*_] | *x"):
    rejects(pattern)

# A '+' sign is part of the literal, as '-' is.
def classify(s):
    match s:
        case +1:
            return "one"
        case -1 + 2j:
            return "complex"
        case {+2: _}:
            return "key"
    return "none"
assert_eq([classify(v) for v in (1, -1 + 2j, {2: 0}, 3)], ["one", "complex", "key", "none"])
