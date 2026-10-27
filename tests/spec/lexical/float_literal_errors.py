# spec: reference/lexical_analysis.html#floating-point-literals
# description: Malformed exponents are syntax errors.
from harness import *
try:
    eval("0.E")
except SyntaxError:
   pass
else:
  assert False
