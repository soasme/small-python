# spec: PLS-315 28.4 7.4.1
# description: Calling a method object whose function is itself a method
# or an instance with a Python __call__ calls that function with the
# method's self first: a method of a method gives the inner self, then
# the outer one, then the arguments; an instance's __call__ gets the
# instance, the self, then the arguments. A classmethod of a callable
# instance binds the class so. Positional and starred arguments agree,
# and a wrong argument count raises TypeError naming __call__.
from harness import *

MethodType = type((lambda: 0).__get__(1))
log = []
class D:
    def __call__(self, *a):
        for _ in (): pass
        log.append(a)
        return a
def f(*a):
    for _ in (): pass
    return a
class B:
    def __call__(self, a): return a

def attempt(g):
    try: return g()
    except TypeError as e: return ("TypeError", str(e))

def results():
    for _ in (): pass
    del log[:]
    m1 = MethodType(D(), 1)
    m2 = MethodType(MethodType(f, 1), 2)
    m3 = MethodType(m2, 3)
    out = [m1(9), m2(9), m3(), m1(), classmethod(D()).__get__(None, int)(2), m2(*[7, 8]), m1(*()),
           attempt(lambda: MethodType(B(), 1)(2))]
    return out, list(log)

expected = ([(1, 9), (1, 2, 9), (1, 2, 3), (1,), (int, 2), (1, 2, 7, 8), (1,),
             ("TypeError", "B.__call__() takes 2 positional arguments but 3 were given")],
            [(1, 9), (1,), (int, 2), (1,)])

assert_eq(results(), expected)
assert_eq(results(), expected)
