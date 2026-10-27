# spec: reference/lexical_analysis.html#indentation
# description: INDENT/DEDENT generation, tabs, and inconsistent indentation errors.
from harness import *

ns = run("def perm(l):\n"
         "        # Compute the list of all permutations of l\n"
         "    if len(l) <= 1:\n"
         "                  return [l]\n"
         "    r = []\n"
         "    for i in range(len(l)):\n"
         "             s = l[:i] + l[i+1:]\n"
         "             p = perm(s)\n"
         "             for x in p:\n"
         "              r.append(l[i:i+1] + x)\n"
         "    return r\n")
assert_eq(len(ns["perm"]([1, 2, 3])), 6)

# Unexpected indent / dedent to an unknown level / missing indent.
assert_syntax_error(" x = 1\n", exception=IndentationError)
assert_syntax_error("if 1:\n        a = 1\n    b = 2\n", exception=IndentationError)
assert_syntax_error("if 1:\na = 1\n", exception=IndentationError)
assert_syntax_error("def f():\n    return 1\n  x = 2\n", exception=IndentationError)

# Tabs are replaced to the next multiple of eight; mixing that depends on
# tab size is a TabError.
assert_eq(run("if 1:\n\ta = 1\n\tb = 2\n")["b"], 2)
assert_eq(run("if 1:\n        a = 1\n        b = a + 1\n")["b"], 2)
assert_syntax_error("if 1:\n\ta = 1\n        b = 2\n", exception=TabError)
assert_syntax_error("if 1:\n        a = 1\n\tb = 2\n", exception=TabError)
assert_true(issubclass(TabError, IndentationError))
assert_true(issubclass(IndentationError, SyntaxError))

# Indentation inside brackets is not significant.
ns = run("x = [1,\n2,\n        3]\nif x:\n  y = (4 +\n5)\n")
assert_eq(ns["y"], 9)

# A whole compound statement on one line.
ns = run("if 1: a = 1; b = 2\nwhile 0: pass\nfor i in (): pass\n")
assert_eq(ns["b"], 2)
assert_syntax_error("if 1: if 1: pass\n")

# Deep nesting works.
source = "".join("    " * i + "if True:\n" for i in range(50)) + "    " * 50 + "x = 1\n"
assert_eq(run(source)["x"], 1)
