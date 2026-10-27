# spec: PLS-315 9.3.3
# description: Lambda defaults evaluate in the class body.
from harness import *
class X:
    v = 10
    f = lambda x=v: x
