# spec: PLS-315 19.3.31
# description: print converts each object in order, after writing the
# ones before it, so a loop or an error in an instance's __str__ happens
# between them; inside functions as at module level, an error leaves the
# objects after it unconverted, and a __str__ returning no str raises
# TypeError.
from harness import *

log = []

class Shown:
    def __init__(self, name, fails=False): self.name = name; self.fails = fails
    def __str__(self):
        for _ in range(2): pass
        log.append(self.name)
        if self.fails: raise KeyError(self.name)
        return self.name

class Wrong:
    def __str__(self): return 1

class Text(str):
    def __str__(self):
        log.append("text")
        return "t"

class Plain:
    pass

class Unset:
    __str__ = None

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def show():
    del log[:]
    print(Shown("a"), 1, Shown("b"), Text("x"))
    out = [error(lambda: print(Shown("c"), Shown("d", True), Shown("e"))),
           error(lambda: print("w", Wrong(), Shown("f"))), error(lambda: print(Unset(), Shown("k")))]
    print(Plain(), 1)
    print("no instance")
    return out + [list(log)]

expected = [("KeyError", "'d'"), ("TypeError", "Wrong.__str__() must return a str, not int"),
            ("TypeError", "'NoneType' object is not callable"),
            ["a", "b", "text", "c", "d"]]
assert_eq(show(), expected)
del log[:]
assert_eq(error(lambda: print(Shown("g"), Shown("h", True), Shown("i"))), ("KeyError", "'h'"))
print(Shown("j"))
assert_eq(log, ["g", "h", "j"])
