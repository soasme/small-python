# spec: PLS-315 9.7
# description: An instance whose last reference goes calls its class's
# Python __del__ once before the next statement runs; the objects its
# reclamation frees are finalized before the next dead sibling (a list
# releasing its items from the last), an exception escaping __del__ does not
# reach the code around it, and an object __del__ makes reachable again
# stays. Finalizers that loop run in function statements as at module level.
from harness import *

log = []
saved = []

class Node:
    def __init__(self, name, child=None):
        self.name, self.child = name, child
    def __del__(self):
        for _ in range(2): pass
        log.append(self.name)
        if self.name == "raise": raise KeyError("ignored")
        if self.name == "phoenix": saved.append(self)

def finalizes():
    del log[:]
    Node("temporary")
    log.append("after temporary")
    x = Node("rebound")
    x = None
    log.append("after rebound")
    pair = [Node("a", Node("a1")), Node("b", Node("b1"))]
    del pair
    log.append("after pair")
    try:
        Node("raise")
        log.append("after raise")
    except KeyError:
        log.append("caught")
    Node("phoenix")
    log.append(len(saved))
    for i in range(3):
        Node(i)
    log.append("after loop")
    return list(log)

expected = ["temporary", "after temporary", "rebound", "after rebound",
            "b", "b1", "a", "a1", "after pair", "raise", "after raise",
            "phoenix", 1, 0, 1, 2, "after loop"]
assert_eq(finalizes(), expected)
saved.clear()
host.collect()
assert_eq(log[-1], "after loop")
del log[:]
Node("module")
assert_eq(log, ["module"])
