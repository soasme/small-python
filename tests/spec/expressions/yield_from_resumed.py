# spec: PLS-315 13.16.3, 27.2.2
# description: a generator suspended in a yield from of a builtin
# iterator, or of an instance with a Python __next__, after an earlier
# yield statement or not, gives the rest of the iterator's items to the
# loop or consumer that resumes it, then goes on after the yield from;
# send() and throw() still reach it there, and an instance's error
# propagates. Inside functions as at module level.
from harness import *

log = []

class Counted:
    def __init__(self, n): self.n = n; self.i = 0
    def __iter__(self): return self
    def __next__(self):
        for _ in (): pass
        self.i += 1
        if self.i > self.n: raise StopIteration
        if self.i == 99: raise KeyError("k")
        return self.i

def gen(source, first):
    if first: yield "a"
    yield from source
    log.append("after")
    yield "z"

def resumed():
    out = []
    for first in (False, True):
        for source in (lambda: [4, 5], lambda: iter((6, 7)), lambda: map(str, [8, 9]), lambda: range(2), lambda: Counted(2)):
            g = gen(source(), first)
            out.append(next(g))
            out.append(list(g))
            out.append([x for x in gen(source(), first)])
            out.append(sum(1 for _ in gen(source(), first)))
    return out

expected = [4, [5, "z"], [4, 5, "z"], 3, 6, [7, "z"], [6, 7, "z"], 3, "8", ["9", "z"], ["8", "9", "z"], 3, 0, [1, "z"], [0, 1, "z"], 3,
            1, [2, "z"], [1, 2, "z"], 3,
            "a", [4, 5, "z"], ["a", 4, 5, "z"], 4, "a", [6, 7, "z"], ["a", 6, 7, "z"], 4, "a", ["8", "9", "z"], ["a", "8", "9", "z"], 4,
            "a", [0, 1, "z"], ["a", 0, 1, "z"], 4, "a", [1, 2, "z"], ["a", 1, 2, "z"], 4]
assert_eq(resumed(), expected)
assert_eq(log, ["after"] * 30)
assert_eq(resumed(), expected)
log.clear()

def sent():
    g = gen(iter((1, 2, 3)), True)
    out = [next(g), next(g), g.send(None)]
    try: g.send(5)
    except AttributeError as e: out.append(str(e))
    g = gen([1, 2], True)
    out += [next(g), next(g)]
    try: g.throw(ValueError("v"))
    except ValueError as e: out.append(e.args)
    g = gen(Counted(200), False)
    for _ in range(98): next(g)
    try: list(g)
    except KeyError as e: out.append(e.args)
    return out

assert_eq(sent(), ["a", 1, 2, "'tuple_iterator' object has no attribute 'send'", "a", 1, ("v",), ("k",)])
assert_eq(log, [])
g = gen(Counted(3), True)
assert_eq((next(g), list(g)), ("a", [1, 2, 3, "z"]))
