# spec: PLS-315 19.3.31
# description: print called with starred objects writes each one's str in
# turn, calling an instance's Python __str__, which may loop, as it reaches
# it, separated by sep and followed by end, to file's write; an error
# from __str__ propagates once the objects before it are written, and an
# unknown keyword raises TypeError before any is. Inside functions as at
# module level.
from harness import *

log = []

class S:
    def __init__(self, v): self.v = v
    def __str__(self):
        for _ in (): pass
        log.append(("str", self.v))
        return "s%d" % self.v

class Bad:
    def __str__(self):
        for _ in (): pass
        raise KeyError("s")

class File:
    def __init__(self): self.parts = []
    def write(self, s): log.append(("write", s)); self.parts.append(s)

def prints():
    f = File()
    a = [S(1), 2, S(3)]
    print(*a, file=f)
    print(*a, *[S(4)], sep="-", end="!", file=f)
    print(*(), file=f)
    out = [f.parts[:], log[:]]
    log.clear()
    g = File()
    try: print(*[1, Bad(), S(5)], file=g)
    except KeyError as e: out.append((e.args, g.parts))
    try: print(*[S(6)], bad=1)
    except TypeError as e: out.append(str(e))
    out.append(log[:])
    log.clear()
    return out

assert_eq(prints(), [
    ["s1", " ", "2", " ", "s3", "\n", "s1", "-", "2", "-", "s3", "-", "s4", "!", "\n"],
    [("str", 1), ("write", "s1"), ("write", " "), ("write", "2"), ("write", " "), ("str", 3), ("write", "s3"), ("write", "\n"),
     ("str", 1), ("write", "s1"), ("write", "-"), ("write", "2"), ("write", "-"), ("str", 3), ("write", "s3"),
     ("write", "-"), ("str", 4), ("write", "s4"), ("write", "!"), ("write", "\n")],
    (("s",), ["1", " "]),
    "print() got an unexpected keyword argument 'bad'",
    [("write", "1"), ("write", " ")],
])
