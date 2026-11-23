# spec: PLS-315 28.3, 13.10.1
# description: A FrameLocalsProxy's subscript, in and not in, given a key
# whose __hash__ is native but whose __eq__ is Python, find a local
# variable the key equals, or an extra local stored under the key, and
# answer at once when there is none; at module level and in functions.
from harness import *
class EqKey:
    __hash__ = object.__hash__
    def __init__(self): self.calls = 0
    def __eq__(self, other):
        self.calls += 1
        return self is other
class NameKey(str):
    __hash__ = str.__hash__
    def __eq__(self, other): return str.__eq__(self, other)
def suspended():
    a = 1
    yield
g = suspended(); next(g)
proxy = g.gi_frame.f_locals
absent = EqKey()
assert_eq([absent in proxy, absent not in proxy], [False, True])
assert_raises(KeyError, lambda: proxy[absent])
stored = EqKey()
proxy[stored] = 7
assert_eq([proxy[stored], stored in proxy, stored not in proxy, absent in proxy], [7, True, False, False])
assert_eq([NameKey("a") in proxy, proxy[NameKey("a")], NameKey("b") in proxy], [True, 1, False])
def inside():
    other = EqKey()
    return [other in proxy, stored in proxy, proxy[stored], NameKey("a") not in proxy]
assert_eq(inside(), [False, True, 7, False])
