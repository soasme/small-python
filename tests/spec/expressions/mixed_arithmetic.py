# spec: PLS-315 7.6.2, 22.3.2
# description: int and float operands convert to float.
from harness import *
x = 1
y = 1.1
assert x + y == 2.1
# print(x+y)

x = 1.1
y = 1
assert x + y == 2.1
# print(x+y)

x = 1.1
y = 2.1
assert x + y == 3.2
# print(x+y)

x = "ab"
y = "cd"
assert x + y == "abcd"
# print(x+y)

x = 2
y = 3
assert x**y == 8
# print(x**y)

x = 2.0
y = 3
assert x**y == 8.0
# print(x**y)

x = 2
y = 3.0
assert x**y == 8.0
# print(x**y)

x = 2.0
y = 3.0
assert x**y == 8.0
# print(x**y)
