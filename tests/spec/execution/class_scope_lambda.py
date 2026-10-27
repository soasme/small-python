# spec: reference/executionmodel.html#resolution-of-names
# description: Lambda defaults evaluate in the class body.
from harness import *
class X:
    v = 10
    f = lambda x=v: x
