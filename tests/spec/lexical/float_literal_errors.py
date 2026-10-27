# spec: PLS-315 12.6
# description: Malformed exponents are syntax errors.
from harness import *
try:
    eval("0.E")
except SyntaxError:
   pass
else:
  assert False
