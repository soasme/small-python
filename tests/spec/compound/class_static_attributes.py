# spec: PLS-315 16.4
# description: a class's __static_attributes__ names, sorted, each n for
# which code whose nearest enclosing class it is stores to self.n, self a
# name: by assignment, annotated assignment with a value, a for or with
# target, unpacking or comprehension target; not by augmented assignment
# or deletion. A list, set or dict comprehension's code is that of the
# scope it is in, so in a class body it is the class's own; the class
# body's own code counts for the class around it.
from harness import *

class C:
    def f(self):
        self.a += 1; self.b = 1; self.c: int; self.d: int = 1
        del self.e
        self.f.g = 1; self[0] = 1
        for self.h in []: pass
        (self.i, [self.j, *self.k]) = 1, (2, 3)
    def g(this): this.m = 1
    q = lambda: [0 for self.n in []]
    w = [0 for self.o in []]
assert_eq(C.__static_attributes__, ("b", "d", "h", "i", "j", "k", "n"))

class A:
    if 0: self.a = 1
    class B:
        if 0: self.b = 1
        w = [0 for self.c in []]
        def g(self): self.d = 1
    def f(self):
        class D:
            if 0: self.e = 1
            def h(self): self.f = 1
        self.g = 1
        w = [0 for self.h in []]
    w = [[0 for self.i in []] for x in []]
    v = [(0 for self.j in []) for x in []]
    if 0: self.l += 1
assert_eq((A.__static_attributes__, A.B.__static_attributes__), (("b", "c", "e", "g", "h", "j"), ("d",)))
