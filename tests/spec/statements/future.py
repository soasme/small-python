# spec: PLS-315 14.13, 16.6.4
# description: Future statements must come first, name a known feature, and only some have effects.
from harness import *

for feature in ("nested_scopes", "generators", "division", "absolute_import", "with_statement",
                "print_function", "unicode_literals", "generator_stop", "annotations", "barry_as_FLUFL"):
    assert_compiles(f"from __future__ import {feature}\n")
assert_compiles('"""doc"""\n# comment\n\nfrom __future__ import annotations\nfrom __future__ import division\nx = 1\n')
assert_compiles("from __future__ import (division,\n    annotations)\n")
assert_compiles("from __future__ import division as d\n")
late = "from __future__ imports must occur at the beginning of the file"
assert_eq(assert_syntax_error("x = 1\nfrom __future__ import annotations\n").msg, late)
assert_eq(assert_syntax_error('"""doc"""\n"""two"""\nfrom __future__ import annotations\n').msg, late)
assert_eq(assert_syntax_error("def f():\n    from __future__ import annotations\n").msg, late)
assert_eq(assert_syntax_error("from __future__ import spam\n").msg, "future feature spam is not defined")
assert_eq(assert_syntax_error("from __future__ import braces\n").msg, "not a chance")
assert_eq(assert_syntax_error("from __future__ import *\n").msg, "future feature * is not defined")

# annotations: every annotation is the string of its source text.
ns = run("from __future__ import annotations\nx: undefined[int] = 1\n"
         "def f(a: list[ int ], *b: Q) -> 1 + 2: pass\nclass C:\n    y: 'quoted'\n")
assert_eq(ns["__annotations__"], {"x": "undefined[int]"})
assert_eq(ns["f"].__annotations__, {"a": "list[int]", "b": "Q", "return": "1 + 2"})
assert_eq(ns["C"].__annotations__, {"y": "'quoted'"})

# barry_as_FLUFL: <> is inequality and != is a syntax error.
ns = run("from __future__ import barry_as_FLUFL\nr = 1 <> 2\n")
assert_eq(ns["r"], True)
assert_syntax_error("from __future__ import barry_as_FLUFL\nr = 1 != 2\n")
assert_syntax_error("r = 1 <> 2\n")

# The other features change nothing.
ns = run("from __future__ import division\nr = 1 / 2\n")
assert_eq(ns["r"], 0.5)
