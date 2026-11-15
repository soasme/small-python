# spec: PLS-315 14.3, 25.5.4
# description: an augmented assignment list += source of a generator, a
# map or an iterator of a Python __next__ runs the source's body, which
# may loop, extending the list itself in place, asking an iterator's
# __length_hint__ first as list.extend does; the target, a name, an
# attribute or a subscription, is stored the same list. An error from the
# source propagates, the items taken before it kept. Inside functions as
# at module level.
from harness import *

log = []

def g(n):
    for i in range(n):
        log.append(i)
        if i == 9: raise KeyError("g")
        yield i

class It:
    def __init__(self): self.n = 0
    def __iter__(self): return self
    def __next__(self):
        for _ in (): pass
        self.n += 1
        if self.n > 2: raise StopIteration
        return self.n
    def __length_hint__(self):
        log.append("hint")
        return 2

class O: pass

def augments():
    b = [7]
    kept = b
    b += g(2)
    b += (x * 2 for x in range(3))
    o = O(); o.l = [1]
    o.l += g(1)
    d = {"k": [5]}
    d["k"] += It()
    m = [0]; m += map(lambda v: v + 1, [1, 2])
    e = [1]
    try: e += g(10)
    except KeyError: pass
    z = [0]; z[0:0] += g(2)
    return b, kept is b, o.l, d, m, len(e), z

expected = ([7, 0, 1, 0, 2, 4], True, [1, 0], {"k": [5, 1, 2]}, [0, 2, 3], 10, [0, 1, 0])
assert_eq(augments(), expected)
assert_eq(log, [0, 1, 0, "hint", 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1])
log.clear()

a = [0]
a += g(3)
assert_eq((a, log), ([0, 0, 1, 2], [0, 1, 2]))
