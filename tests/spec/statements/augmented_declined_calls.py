# spec: PLS-315 7.6.3, 7.6.2, 14.3
# description: an augmented assignment whose Python in-place method returns
# NotImplemented applies the plain operator: the left operand's Python
# method, then the right operand's reflected one, a subclass's first; an
# unsupported pair names the augmented operator, and an error from either
# method propagates; inside functions, generators and at module level.
from harness import *

log = []

class A:
    def __iadd__(self, o): log.append("iadd"); return NotImplemented
    def __imul__(self, o): log.append("imul"); return NotImplemented
    def __add__(self, o):
        for _ in range(1): pass
        log.append(("add", o)); return NotImplemented if o == 9 or isinstance(o, B) else ("add", o)
    def __mul__(self, o): log.append(("mul", o)); return NotImplemented
    def __repr__(self): return "A"

class B:
    def __radd__(self, o):
        for _ in range(1): pass
        log.append("radd"); return "radd"
    def __rmul__(self, o): log.append("rmul"); return "rmul"
    def __repr__(self): return "B"

class Sub(A):
    def __radd__(self, o): log.append("sub.radd"); return "sub"

class Raising(A):
    def __add__(self, o): raise KeyError(o)

def assigns():
    out = []
    x = A(); x += 1; out.append(x)
    x = A(); x += B(); out.append(x)
    x = A(); x *= B(); out.append(x)
    x = A(); x += Sub(); out.append(x)
    out.append(log[:]); log.clear()
    x = A()
    try: x += 9
    except TypeError as e: out.append(str(e))
    x = A()
    try: x *= 2
    except TypeError as e: out.append(str(e))
    x = Raising()
    try: x += 1
    except KeyError as e: out.append(("key", e.args))
    out.append(log[:]); log.clear()
    return out

expected = [
    ("add", 1), "radd", "rmul", "sub",
    ["iadd", ("add", 1), "iadd", ("add", "B"), "radd", "imul", ("mul", "B"), "rmul",
     "iadd", "sub.radd"],
    "unsupported operand type(s) for +=: 'A' and 'int'",
    "unsupported operand type(s) for *=: 'A' and 'int'",
    ("key", (1,)),
    ["iadd", ("add", 9), "imul", ("mul", 2), "iadd"],
]
assert_eq(repr(assigns()), repr(expected).replace("'B'", "B"))
x = A(); x += B()
assert_eq((x, log[0], log[2]), ("radd", "iadd", "radd"))
log.clear()

# In a generator, with the right operand sent in.
def gen():
    x = A()
    x += (yield "first")
    yield x

g = gen()
assert_eq(next(g), "first")
assert_eq(g.send(B()), "radd")
assert_eq(log[0], "iadd")
assert_eq(log[2], "radd")
