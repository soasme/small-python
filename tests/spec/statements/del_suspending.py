# spec: PLS-315 14.7, 27.2
# description: del targets whose subexpressions yield: the object and key are evaluated in order, then deleted.
from harness import *

log = []
class Box:
    def __init__(self):
        self.x = 1
    def __delitem__(self, key):
        log.append(("delitem", key))
    def __delattr__(self, name):
        log.append(("delattr", name))

box = Box()
def holder():
    log.append("holder")
    return box

def gen():
    del holder()[(yield "key")], holder().x
    del [holder()[(yield "first")], (holder()[(yield "second")])]

g = gen()
assert_eq(next(g), "key")
assert_eq(log, ["holder"])
assert_eq(g.send(1), "first")
assert_eq(log, ["holder", ("delitem", 1), "holder", ("delattr", "x"), "holder"])
log.clear()
assert_eq(g.send(2), "second")
assert_eq(log, [("delitem", 2), "holder"])
assert_raises(StopIteration, g.send, 3)
assert_eq(log, [("delitem", 2), "holder", ("delitem", 3)])

# A failing deletion raises at the point of deletion.
d = {}
def failing():
    del d[(yield)]
g = failing()
next(g)
e = assert_raises(KeyError, g.send, "missing")
assert_eq(e.args, ("missing",))
