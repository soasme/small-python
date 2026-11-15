# spec: PLS-315 13.3.3, 14.2, 25.4.2
# description: a store of a generator to a list's slice whose parts have
# a Python __index__ calls the step's, the start's and the stop's
# __index__ first, then runs the generator's body, both of which may
# loop, and stores its items; an extended slice still needs as many
# items, and the generator's error propagates, the list as it was. A
# chained assignment stores the same generator to the other targets.
# Inside functions as at module level.
from harness import *

log = []

class I:
    def __init__(self, n): self.n = n
    def __index__(self):
        for _ in (): pass
        log.append(self.n)
        return self.n

def items(k):
    for x in k:
        log.append(x)
        if x == "!": raise KeyError("g")
        yield x

def stores():
    b = [0, 1, 2, 3]
    b[I(0):I(4):I(2)] = items("xy")
    try: b[I(1):] = items("q!")
    except KeyError: pass
    c = d = [5, 6]
    c[:I(1)] = e = items("z")
    try: b[::I(2)] = items("abc")
    except ValueError as error: message = str(error)
    return b, c, d, list(e), message

expected = (["x", 1, "y", 3], ["z", 6], ["z", 6], [], "attempt to assign sequence of size 3 to extended slice of size 2")
assert_eq(stores(), expected)
assert_eq(log, [2, 0, 4, "x", "y", 1, "q", "!", 1, "z", 2, "a", "b", "c"])
log.clear()

a = list(range(6))
a[I(1):I(3)] = items("ab")
assert_eq((a, log), ([0, "a", "b", 3, 4, 5], [1, 3, "a", "b"]))
