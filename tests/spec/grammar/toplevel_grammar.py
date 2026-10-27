# spec: PLS-315 A.2, 17.6
# description: The start rules of Annex A: file, interactive, and eval input, and simple_stmts.
from harness import *

# file: [statements] ENDMARKER
assert_compiles("")
assert_compiles("\n\n")
assert_compiles("x = 1\ny = 2")
assert_compiles("if x:\n    pass\nx = 1\n")
# simple_stmts: ';'.simple_stmt+ [';'] NEWLINE
assert_compiles("x = 1; y = 2;\n")
assert_syntax_error("x = 1;; y = 2\n")
assert_syntax_error(";\n")
assert_syntax_error("x = 1; if x: pass\n")
assert_syntax_error("if x: pass; else: pass\n")

# eval: expressions NEWLINE* ENDMARKER
assert_eq(eval(compile("1, 2", "<spec>", "eval")), (1, 2))
assert_eq(eval(compile("1\n\n", "<spec>", "eval")), 1)
assert_syntax_error("*[1], 2", "eval")
assert_syntax_error("x = 1", "eval")
assert_syntax_error("1; 2", "eval")
assert_syntax_error("pass", "eval")
assert_syntax_error("1\n2", "eval")

# interactive: statement_newline, one statement (simple or compound) at a time.
assert_compiles("x = 1; y = 2\n", "single")
assert_compiles("if 1:\n    pass\n\n", "single")
assert_syntax_error("", "single")
assert_syntax_error("\n", "single")
assert_syntax_error("# comment\n", "single")
assert_compiles("*a, b\n", "single")
assert_syntax_error("x = 1\ny = 2\n", "single")
