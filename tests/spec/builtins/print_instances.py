# spec: PLS-315 19.3.31
# description: print converts each object in order, after writing the
# ones before it and its separator, so a loop or an error in an
# instance's __str__ happens between the writes; inside functions as at
# module level, with sep, end, file and flush or without, an error leaves
# the objects after it unconverted, a __str__ returning no str raises
# TypeError, and a wrong sep or end raises before any conversion.
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

class Sink:
    def write(self, text): log.append("w" + text)
    def flush(self): log.append("flush")

def keywords():
    del log[:]
    sink = Sink()
    print(Shown("a"), 1, Shown("b"), sep="-", end="!", file=sink, flush=True)
    print(Shown("c"), file=sink, sep=None, end=None)
    print(file=sink)
    print(Shown("d"), file=None, end="")
    out = [error(lambda: print(Shown("e"), Shown("f", True), Shown("g"), file=sink)),
           error(lambda: print(Shown("h"), sep=1)), error(lambda: print(Shown("i"), end=b"")),
           error(lambda: print(Shown("j"), spam=1))]
    return out + [list(log)]

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
expected = [("KeyError", "'f'"), ("TypeError", "sep must be None or a string, not int"),
            ("TypeError", "end must be None or a string, not bytes"),
            ("TypeError", "print() got an unexpected keyword argument 'spam'"),
            ["a", "wa", "w-", "w1", "w-", "b", "wb", "w!", "flush", "c", "wc", "w\n", "w\n", "d",
             "e", "we", "w ", "f"]]
assert_eq(keywords(), expected)
del log[:]
print(Shown("k"), Shown("l"), sep="+", file=Sink())
assert_eq(log, ["k", "wk", "w+", "l", "wl", "w\n"])
del log[:]
assert_eq(error(lambda: print(Shown("g"), Shown("h", True), Shown("i"))), ("KeyError", "'h'"))
print(Shown("j"))
assert_eq(log, ["g", "h", "j"])
