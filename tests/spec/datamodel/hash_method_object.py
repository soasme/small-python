# spec: PLS-315 7.5.7, 26.1.2
# description: a class whose __hash__ is a method object of another
# instance hashes its instances by calling that method with no argument,
# its own self bound: in dict and set displays, item stores, lookups and
# set methods, inside functions and generators as at module level.
from harness import *

log = []
class Hasher:
    def __init__(self, n): self.n = n
    def hash(self, *args):
        for _ in (): pass
        log.append((self.n, len(args)))
        return 7
class H:
    __hash__ = Hasher("h").hash
    def __eq__(self, other): return self is other

def cases():
    del log[:]
    a, b = H(), H()
    d = {a: 1}
    s = {b}
    d[b] = 2
    found = (a in d, b in s, a in s)
    s.add(a)
    u = set().union([a, b])
    return found, len(d), len(s), len(u), list(log)

expected = ((True, True, False), 2, 2, 2, [("h", 0)] * 9)
assert_eq(cases(), expected)

def gen():
    yield cases()
assert_eq(next(gen()), expected)
