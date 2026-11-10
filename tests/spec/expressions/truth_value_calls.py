# spec: PLS-315 7.5.1, 13.12, 20.3
# description: not x and bool(x) of an instance call its class's Python
# __bool__ once: not inverts the bool it returns and bool() returns it;
# a value other than a bool is a TypeError naming the class, and an
# exception from __bool__ propagates, in an expression, an assignment, a
# call's argument and a display, and an if tests the same truth. A class
# with no __bool__ calls its Python __len__ alike, the length's truth
# being the value's, a negative or non-integer length a ValueError or
# TypeError, and a __len__ that cannot take the value's call a TypeError,
# inside functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Truth:
    def __init__(self, v): self.v = v
    def __bool__(self):
        spin()
        log.append(self.v)
        if self.v == "raise": raise KeyError("bool")
        return 1 if self.v == "int" else self.v

class Sized:
    def __init__(self, n): self.n = n
    def __len__(self):
        spin()
        log.append(("len", self.n))
        if self.n == "raise": raise KeyError("len")
        return self.n

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    yes, no = Truth(True), Truth(False)
    flipped = not yes
    made = bool(no)
    out = [flipped, made, not no, bool(yes), str(not yes), str(bool(yes)), [not no, bool(no)]]
    out += [error(lambda: not Truth("int")), error(lambda: bool(Truth("int"))), error(lambda: not Truth("raise")),
            error(lambda: bool(Truth("raise")))]
    if no: out.append("taken")
    else: out.append("skipped")
    empty, full = Sized(0), Sized(2)
    out.append([not empty, bool(full), bool(empty), not full, [i for i in "ab" if full], "yes" if empty else "no"])
    out += [error(lambda: bool(Sized(-1))), error(lambda: not Sized("3")), error(lambda: bool(Sized("raise")))]
    out.append(list(log))
    return out

expected = [False, False, True, True, "False", "True", [True, False],
            ("TypeError", "Truth.__bool__() must return a bool, not int"),
            ("TypeError", "Truth.__bool__() must return a bool, not int"), ("KeyError", "'bool'"), ("KeyError", "'bool'"), "skipped",
            [True, True, False, False, ["a", "b"], "no"],
            ("ValueError", "__len__() should return >= 0"), ("TypeError", "'str' object cannot be interpreted as an integer"),
            ("KeyError", "'len'"),
            [True, False, False, True, True, True, False, False, "int", "int", "raise", "raise", False,
             ("len", 0), ("len", 2), ("len", 0), ("len", 2), ("len", 2), ("len", 2), ("len", 0),
             ("len", -1), ("len", "3"), ("len", "raise")]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)

class Arity:
    def __len__(self, extra):
        spin()
        return 0

missing = "Arity.__len__() missing 1 required positional argument: 'extra'"
assert_eq([error(lambda: not Arity()), error(lambda: bool(Arity()))], [("TypeError", missing)] * 2)
