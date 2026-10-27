# spec: PLS-315 15.2
# description: while loops with else and break.
from harness import *
# i = 0
# while i < 5:
#   i += 1
#   # print(i)
# assert i == 5

i = 0
while i < 5:
  i += 1
  # print(i)
  if i == 3:
      break
assert i == 3
