# spec: PLS-315 13.11
# description: and/or skip evaluating the right operand.
from harness import *

# Test various cases of short circuit evaluation:

run = 1
timeTaken = 33
r = (11, 22, run, run != 1 and "s" or "", timeTaken)
print(r)
assert r == (11, 22, 1, '', 33)


run = 0
r = (11, 22, run, run != 1 and "s" or "", timeTaken)
print(r)
assert r == (11, 22, 0, 's', 33)

