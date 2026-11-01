# spec: PLS-315 A.8, 14.2, 14.5
# description: The target grammar of Annex A: star_targets, single_target, del_targets, and t_primary chains.
from harness import *

valid = [
    "a = 1", "a, = 1,", "a, b = 1, 2", "(a, b) = 1, 2", "[a, b] = 1, 2", "[a, *b] = 1, 2",
    "*a, b = 1, 2", "(a) = 1", "((a), (b)) = 1, 2", "[] = ()", "() = []", "[(a)] = [1]",
    "a.b = 1", "a[0] = 1", "a[0:1, ::2] = 1", "a().b = 1", "a(x for x in y).b = 1",
    "a.b.c[d](e).f = 1", "[a.b, c[0]] = 1, 2", "for a.b, *c[0] in x: pass",
    "with x as (a, [b, *c]): pass", "a, *(b, c) = 1, 2, 3",
    "a += 1", "a.b += 1", "a[0] += 1", "(a) += 1", "a: int = 1", "a.b: int", "a[0]: int",
    "(a): int = 1",
    "del a", "del a,", "del a, b", "del (a), [b]", "del (a, b), [c, [d]]", "del a.b, a[0], a()[0]",
    "del ()", "del []",
]
for source in valid:
    assert_compiles(source + "\n")

invalid = [
    "a() = 1", "1 = a", "a + b = 1", "*a = 1", "**a = 1", "a, **b = 1", "*a, *b = 1, 2",
    "f(x for x in y) = 1", "(a, b) += 1", "[a] += 1", "a, b += 1", "*a += 1", "a() += 1",
    "(a, b): int", "[a]: int", "*a: int", "a, b: int",
    "del *a", "del a()", "del f(x)", "del (*a, b)", "del a + b", "del 1",
    "for a() in x: pass", "with x as a(): pass", "[*a, *b] = 1, 2",
    "(a := 1) = 2", "a if b else c = 1", "lambda: a = 1", "yield = 1", "await x = 1",
]
for source in invalid:
    assert_syntax_error(source + "\n")
# invalid_with_item: an expression that ends a with item is its target.
for source, message, offset, end_offset in (
        ("with a as b < c: pass", "cannot assign to comparison", 11, 16),
        ("with a as b if c else d: pass", "cannot assign to conditional expression", 11, 24),
        ("with (a as b + c, d): pass", "cannot assign to expression", 12, 17),
        ("with a as b, c as d < e: pass", "cannot assign to comparison", 19, 24),
        ("with a as lambda: 1: pass", "cannot assign to lambda", 11, 20),
        ("with a as not b: pass", "cannot assign to expression", 11, 16),
        ("with a as 1: pass", "cannot assign to literal", 11, 12),
        ("with a as *b: pass", "starred assignment target must be in a list or tuple", 11, 13),
        ("with a as b c: pass", "invalid syntax", 13, 14),
        ("with a as b := 1: pass", "invalid syntax", 13, 15)):
    error = assert_syntax_error(source)
    assert_eq((error.msg, error.offset, error.end_offset), (message, offset, end_offset), source)
