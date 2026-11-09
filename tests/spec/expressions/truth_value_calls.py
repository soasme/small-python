# spec: PLS-315 7.5.1, 13.12, 20.3
# description: not x and bool(x) of an instance call its class's Python
# __bool__ once: not inverts the bool it returns and bool() returns it;
# a value other than a bool is a TypeError naming the class, and an
# exception from __bool__ propagates, in an expression, an assignment, a
# call's argument and a display, and an if tests the same truth, inside
# functions as at module level.
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
    out.append(list(log))
    return out

expected = [False, False, True, True, "False", "True", [True, False],
            ("TypeError", "Truth.__bool__() must return a bool, not int"),
            ("TypeError", "Truth.__bool__() must return a bool, not int"), ("KeyError", "'bool'"), ("KeyError", "'bool'"), "skipped",
            [True, False, False, True, True, True, False, False, "int", "int", "raise", "raise", False]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
