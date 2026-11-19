# spec: PLS-315 9.7
# description: When an object dies, its __del__ runs first, then the
# callback of a host weak reference to it, given the reference, before the
# next statement: a Python callback may loop, pause in a generator, let
# another object die, whose callback runs after it, and raise, its
# exception reported and not propagated, as is the TypeError of a callback
# that takes no argument. Inside functions as at module
# level.
from harness import *

log = []
class Node:
    def __init__(self, name): self.name = name
class Dying(Node):
    def __del__(self):
        for _ in range(2): pass
        log.append(("del", self.name))
def callback(name, then=None, fail=False):
    def called(ref):
        for _ in range(2): pass
        log.append(("callback", name, ref() is None))
        if then: then.pop()
        if fail: raise LookupError(name)
    return called

def run():
    del log[:]
    a, b = Node("a"), Dying("b")
    refs = [host.weak_reference(a, callback("a")), host.weak_reference(b, callback("b"))]
    del a
    log.append("after a")
    del b
    log.append("after b")
    held = [Node("inner")]
    c = Node("c")
    refs.append(host.weak_reference(held[0], callback("inner")))
    refs.append(host.weak_reference(c, callback("c", then=held, fail=True)))
    del c
    log.append("after c")
    d = Node("d")
    refs.append(host.weak_reference(d, lambda: log.append("never")))
    del d
    log.append("after d")
    return list(log)

expected = [("callback", "a", True), "after a", ("del", "b"), ("callback", "b", True), "after b",
            ("callback", "c", True), ("callback", "inner", True), "after c", "after d"]

def paused():
    def gen():
        x = Node("g")
        ref = host.weak_reference(x, callback("g"))
        yield 1
        del x
        yield 2
    del log[:]
    return list(gen()), list(log)

def main():
    return run(), paused()

expected_all = (expected, ([1, 2], [("callback", "g", True)]))
assert_eq(main(), expected_all)
assert_eq((run(), paused()), expected_all)
