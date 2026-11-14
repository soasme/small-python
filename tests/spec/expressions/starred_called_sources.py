# spec: PLS-315 13.2.2, 13.3.4, 27.1.2, 27.1.5, 27.1.6, 27.1.7
# description: a starred item of a list, tuple or set display, or a call's
# starred argument, that is an iterator over a sequence, a reversed
# sequence, a map or filter, or a zip or enumerate of a generator, calls
# the sequence's __getitem__ and __len__, or the function, for each item in
# order, a list or tuple display asking the length hint first; an error from any
# propagates from the display; inside functions as at module level.
from harness import *

log = []

class Seq:
    def __init__(self, n): self.n = n
    def __getitem__(self, i):
        log.append(("item", i))
        if i >= self.n: raise IndexError(i)
        return i * 10
    def __len__(self):
        log.append("len")
        return self.n

def double(x):
    log.append(("f", x))
    return x * 2

def gen(n):
    for i in range(n):
        log.append(("gen", i))
        yield i

def args(*a): return a

def displays():
    out = [[*iter(Seq(2))]]
    out.append(log[:]); log.clear()
    out.append((*reversed(Seq(2)), "end"))
    out.append(log[:]); log.clear()
    out.append({*map(double, [1, 2])})
    out.append(log[:]); log.clear()
    out.append(args(*filter(double, [0, 3]), *zip(gen(2), "ab")))
    out.append(log[:]); log.clear()
    out.append([0, *enumerate(gen(1)), *Seq(1)])
    out.append(log[:]); log.clear()
    return out

expected = [
    [0, 10],
    ["len", ("item", 0), ("item", 1), ("item", 2)],
    (10, 0, "end"),
    ["len", "len", ("item", 1), ("item", 0)],
    {2, 4},
    [("f", 1), ("f", 2)],
    (3, (0, "a"), (1, "b")),
    [("f", 0), ("f", 3), ("gen", 0), ("gen", 1)],
    [0, (0, 0), 0],
    [("gen", 0), "len", ("item", 0), ("item", 1)],
]
assert_eq(displays(), expected)
log.clear()
out = [[*iter(Seq(2))], log[:]]
assert_eq(out, [[0, 10], ["len", ("item", 0), ("item", 1), ("item", 2)]])
log.clear()

# An error from the sequence or the function propagates from the display.
class Bad(Seq):
    def __getitem__(self, i):
        if i == 1: raise KeyError(i)
        return i

def fails(x):
    if x: raise ValueError(x)
    return x

def errors():
    out = []
    try: [*iter(Bad(3))]
    except KeyError as e: out.append(("key", e.args[0]))
    try: (*map(fails, [0, 5]),)
    except ValueError as e: out.append(("value", e.args[0]))
    try: args(*reversed(Bad(3)))
    except KeyError as e: out.append(("key", e.args[0]))
    return out

assert_eq(errors(), [("key", 1), ("value", 5), ("key", 1)])
