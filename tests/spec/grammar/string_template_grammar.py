# spec: PLS-315 A.7, 12.5.6, 12.5.7
# description: The f-string and t-string grammar of Annex A: replacement fields, '=', conversions, and nested format specs.
from harness import *

x, width = 3.25, 8
# '{' annotated_rhs '='? [conversion] [':' format_spec*] '}'
assert_eq(f"{x}", "3.25")
assert_eq(f"{x=}", "x=3.25")
assert_eq(f"{x = }", "x = 3.25")
assert_eq(f"{x=!s}", "x=3.25")
assert_eq(f"{x=:.1f}", "x=3.2")
assert_eq(f"{'a'!r}", "'a'")
assert_eq(f"{'é'!a}", "'\\xe9'")
assert_eq(f"{x:{width}.{1}f}", "     3.2")
assert_eq(f"{x:>{width}}", "    3.25")
assert_eq(f"{x:{'>'}{width}}", "    3.25")
assert_eq(f"{{}}{x}{{", "{}3.25{")
# annotated_rhs: star expressions and yield expressions.
assert_eq(f"{*[1, 2], 3}", "(1, 2, 3)")
assert_eq(f"{1, 2}", "(1, 2)")
def gen():
    return f"{(yield 1)}"
g = gen()
next(g)
assert_eq(assert_raises(StopIteration, g.send, "sent").value, "sent")
assert_eq(f"{(lambda: 5)()}", "5")
assert_eq(f"{x if x else 0}", "3.25")
assert_eq(f"{(y := 4)}", "4")
# Nested f-strings may reuse the same quote.
assert_eq(f"{f"{f"{x}"}"}", "3.25")

invalid = [
    'f"{}"', 'f"{ }"', 'f"{x!}"', 'f"{x!z}"', 'f"{x!r=}"', 'f"{x:{}}"',
    'f"{"', 'f"}"', 'f"{x"', 'f"{x!r:"', 'f"{=}"', 'f"{x!s!r}"', 'f"{*x}"',
    'f"{x:{y:{z:{w}}}}"',
    't"{}"', 't"{x!z}"', 't"{x:{}}"', 't"}"',
]
for source in invalid:
    assert_syntax_error(source, "eval")
# A format spec may nest a replacement field one level; a lambda needs parentheses.
assert_compiles('f"{x:{y:{z}}}"', "eval")
assert_syntax_error('f"{lambda: 1}"', "eval")

# t-strings follow the same grammar.
t = t"{x=:.1f} and {x!r:>{width}}"
assert_eq(t.strings, ("x=", " and ", ""))
assert_eq([(i.expression, i.conversion, i.format_spec) for i in t.interpolations],
          [("x", None, ".1f"), ("x", "r", ">8")])
