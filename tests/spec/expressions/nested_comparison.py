# spec: PLS-315 9.6, 25.5.3, 26
# description: Equality of nested lists, tuples and dicts recurses as deep as the stack allows, then raises RecursionError.
from harness import *

def nest(make, depth):
    value = None
    for _ in range(depth):
        value = make(value)
    return value

# Nesting far past the recursion limit still compares.
for make in (lambda x: [x], lambda x: (x,), lambda x: {"k": x}, lambda x: [1, x]):
    assert nest(make, 5000) == nest(make, 5000)
    assert not (nest(make, 5000) != nest(make, 5000))
    assert nest(make, 5000) != nest(make, 4999)

# Comparing two self-containing values never ends; it raises.
a = []; a.append(a)
b = []; b.append(b)
try:
    a == b
    raise AssertionError("no RecursionError")
except RecursionError:
    pass
d = {}; d[0] = d
e = {}; e[0] = e
try:
    d == e
    raise AssertionError("no RecursionError")
except RecursionError:
    pass
assert a == a and d == d
