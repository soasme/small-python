# spec: PLS-315 19.3.31
# description: print to a file whose write or flush is Python code
# Each write looks up the file's write anew, then converts its value by
# str(), a Python __str__ included, then calls the write; the separator
# goes before every object but the first, the end after the last, and a
# true flush calls the file's flush last. write may be a method, a
# property's or __getattr__'s value, and any of them may loop. A str
# subclass sep or end is accepted and written as its str(). A missing
# write raises before the object's conversion; an error from a __str__,
# a write or a flush propagates, the writes before it done. Inside
# functions as at module level.
from harness import *

log = []

class S:
    def __init__(self, t): self.t = t
    def __str__(self):
        for _ in (): pass
        log.append("str " + self.t)
        return self.t

class File:
    def write(self, text):
        for _ in (): pass
        log.append("w " + text)
        return len(text)
    def flush(self):
        for _ in (): pass
        log.append("flush")

class Lookup:
    def __getattr__(self, name):
        for _ in (): pass
        log.append("get " + name)
        return lambda *a: log.append((name,) + a)

class Prop:
    @property
    def write(self):
        for _ in (): pass
        log.append("prop")
        return lambda text: log.append("p " + text)

class Mark(str):
    def __str__(self):
        for _ in (): pass
        log.append("mark")
        return "+"

class Bad:
    def __str__(self):
        for _ in (): pass
        raise LookupError("str")

class Failing:
    def write(self, text):
        for _ in (): pass
        log.append("w " + text)
        if text == "b": raise LookupError("write")
    def flush(self):
        for _ in (): pass
        raise LookupError("flush")

def prints():
    print(S("a"), [1, S("b")], 3, sep=",", end=".\n", file=File(), flush=True)
    print(S("c"), "d", file=Lookup(), flush=True)
    print(S("e"), file=Prop())
    print(1, 2, sep=Mark("-"), end=Mark("!"), file=File())
    print(file=File())
    return log

expected = ["str a", "w a", "w ,", "w [1, <S>]", "w ,", "w 3", "w .\n", "flush",
            "get write", "str c", ("write", "c"), "get write", ("write", " "), "get write", ("write", "d"),
            "get write", ("write", "\n"), "get flush", ("flush",),
            "prop", "str e", "p e", "prop", "p \n",
            "w 1", "mark", "w +", "w 2", "mark", "w +", "w \n"]
S.__repr__ = lambda self: "<S>"
assert_eq(prints(), expected)
log.clear()
print(S("a"), [1, S("b")], 3, sep=",", end=".\n", file=File(), flush=True)
assert_eq(log, expected[:8])
log.clear()

def errors():
    out = []
    try: print(Bad(), file=File())
    except LookupError as e: out.append(e.args)
    try: print(S("z"), file=object())
    except AttributeError: out.append("attr")
    try: print("a", "b", "c", file=Failing())
    except LookupError as e: out.append(e.args)
    try: print("a", file=Failing(), flush=True)
    except LookupError as e: out.append(e.args)
    return out

assert_eq(errors(), [("str",), "attr", ("write",), ("flush",)])
assert_eq(log, ["w a", "w  ", "w b", "w a", "w \n"])
