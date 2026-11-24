# spec: PLS-315 22.1.8, 18.2.1
# description: A decimal literal over the int string limit is an error as the
#   parser reads it: it ends the parse, ahead of any syntax error the parse
#   meets after or because of it, at its line with offsets 0.
from harness import *

big = "1" + "0" * 5000
limit = "Exceeds the limit (4300 digits) for integer string conversion: value has 5001 digits"

def check(source, line, mode="exec"):
    caught = assert_syntax_error(source, mode)
    assert_eq(caught.msg[:len(limit)], limit, source[:12])
    assert_eq((caught.lineno, caught.offset, caught.end_lineno, caught.end_offset), (line, 0, line, 0), source[:12])

check(f"x = {big}\n", 1)
# A syntax error later in the statement, or an unclosed bracket, loses.
check(f"x = {big} + (\n", 1)
check(f"x = ({big}, 1 +)\n", 1)
check(f"x = [{big} for in]\n", 1)
check(f"def f():\n    x = 1 + {big} + (\n", 2)
check(f"x = ({big}, 1 +\n", 1)
# So does one the parse finds while it explains a failure there.
check(f"x = a {big}\n", 1)
check(f"x = (a {big})\n", 1)
check(f"print {big}\n", 1)
check(f"pass if {big} else x\n", 1)
check(f"match = {big} +\n", 1)
check(f"case {big}: pass\n", 1)
check(f"for {big} in x: pass\n", 1)
check(f"x = (1 +\ny = {big})\n", 2)
# In a formatted string's field, a lambda default, a pattern, an annotation.
check(f'x = f"{{{big}}}" + (\n', 1)
check(f"f = lambda a={big}: (\n", 1)
check(f"match x:\n    case {big}: pass\n", 2)
check(f"from __future__ import annotations\nx: {big} = (\n", 2)
check(f"{big} +", 1, "eval")
check(f"[{big}, ", 1, "eval")
# A syntax error the parse meets before the literal wins.
assert_eq(assert_syntax_error(f"x = 1 2 {big}\n").msg, "invalid syntax")
assert_eq(assert_syntax_error(f"x = = {big}\n").msg, "invalid syntax")
# Bases that are powers of two have no limit.
assert_compiles(f"x = 0x{'f' * 5000}\n")
