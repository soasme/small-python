# spec: PLS-315 19.3.1, 19.3.33, 27.1.7
# description: abs(), round() and reversed() of an instance call its class's
# __abs__, __round__ (with ndigits unless it is None) or __reversed__, which
# may loop, inside functions as at module level, and return the result
# unchecked; their exceptions propagate, a wrong arity is the method's
# TypeError, and with no method each raises its own TypeError.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Shape:
    def __init__(self, tag): self.tag = tag
    def __abs__(self):
        spin()
        log.append(("abs", self.tag))
        if self.tag == "bad":
            raise ValueError("abs")
        return self.tag
    def __round__(self, *args):
        spin()
        log.append(("round",) + args)
        return [self.tag, *args]
    def __reversed__(self):
        spin()
        log.append(("reversed", self.tag))
        return "not an iterator"

class Arity:
    def __abs__(self, extra): spin()

class Derived(Shape): pass

class Plain: pass

class Unreversible:
    __reversed__ = None
    def __len__(self): return 1
    def __getitem__(self, i): return i

def error(f, *args):
    try:
        f(*args)
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    s = Shape("s")
    out = [abs(s), round(s), round(s, None), round(s, 2), round(s, "x"), reversed(s),
           abs(Derived("d")), round(Derived("d"), 1)]
    out += [error(abs, Shape("bad")), error(abs, Arity()), error(round, Arity()),
            error(abs, Plain()), error(round, Plain()), error(reversed, Plain()),
            error(reversed, Unreversible())]
    out.append(list(log))
    return out

expected = ["s", ["s"], ["s"], ["s", 2], ["s", "x"], "not an iterator", "d", ["d", 1],
            ("ValueError", "abs"),
            ("TypeError", "Arity.__abs__() missing 1 required positional argument: 'extra'"),
            ("TypeError", "type Arity doesn't define __round__ method"),
            ("TypeError", "bad operand type for abs(): 'Plain'"),
            ("TypeError", "type Plain doesn't define __round__ method"),
            ("TypeError", "'Plain' object is not reversible"),
            ("TypeError", "'Unreversible' object is not reversible"),
            [("abs", "s"), ("round",), ("round",), ("round", 2), ("round", "x"), ("reversed", "s"),
             ("abs", "d"), ("round", 1), ("abs", "bad")]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
