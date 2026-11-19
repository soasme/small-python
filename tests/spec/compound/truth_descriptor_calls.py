# spec: PLS-315 7.3.2, 7.5.1, 13.10, 13.11, 13.13, 15.1, 15.2
# description: a test (if, while, a conditional expression, and, or,
# not, a comprehension's if), also of a comparison's result, reads a
# __bool__ that a descriptor's Python __get__ gives before calling it;
# an AttributeError of the read makes the object true, any other
# exception propagates, and a result that is no bool raises TypeError.
# Inside functions as at module level.
from harness import *

log = []
class Get:
    def __init__(self, give): self.give = give
    def __get__(self, obj, cls):
        for _ in range(2): pass
        log.append("get")
        if isinstance(self.give, BaseException): raise self.give
        return self.give.__get__(obj, cls)

def falsy(self):
    log.append("bool")
    return False
def bad(self): return 3

def run(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))

def shown(v):
    return type(v).__name__ if type(v).__name__ == "T" else v

def forms(o):
    out = [1 if o else 0, shown(o and 1), shown(o or 2), not o]
    if o: out.append("if")
    n = 0
    while o and n < 2: n += 1
    out += [n, [x for x in (1,) if o], shown(1 < 2 and o)]
    return out

class Eq:
    def __eq__(self, other):
        return type("T", (), {"__bool__": Get(falsy)})()

def results():
    out = []
    for give in (falsy, AttributeError("a"), KeyError("k"), bad):
        T = type("T", (), {"__bool__": Get(give)})
        out += [run(lambda: forms(T())), log[:]]
        log.clear()
    out += [[1 if Eq() == 1 else 0, shown(1 < 2 == Eq()), [x for x in (1,) if Eq() == x]], log[:]]
    log.clear()
    return out

expected = [[0, "T", 2, True, 0, [], "T"], ["get", "bool"] * 7,
            [1, 1, "T", False, "if", 2, [1], "T"], ["get"] * 9,
            ("KeyError", "'k'"), ["get"],
            ("TypeError", "T.__bool__() must return a bool, not int"), ["get"],
            [0, "T", []], ["get", "bool"] * 2]

assert_eq(results(), expected)
def main():
    return results()
assert_eq(main(), expected)
