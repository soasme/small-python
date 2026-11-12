# spec: PLS-315 9.7
# description: When a collection reclaims a cycle, a host weak reference
# to an object of the cycle that the cycle itself holds is garbage too: its
# callback is not called; one held from outside the cycle has its callback
# called, and both are dead afterwards.
from harness import *

called = []
class Node: pass
def cycle():
    a = Node()
    a.self = a
    return a

host.disable_automatic_collection()
inner = cycle()
inner.ref = host.weak_reference(inner, lambda r: called.append("inner"))
outer = cycle()
outside = host.weak_reference(outer, lambda r: called.append("outer"))
del inner, outer
host.collect()
assert_eq(called, ["outer"])
assert_eq(outside(), None)
