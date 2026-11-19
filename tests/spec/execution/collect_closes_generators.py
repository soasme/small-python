# spec: PLS-315 9.7, 27.2.4
# description: An explicit collection closes the unreachable generators it
# reclaims that are suspended inside a try, their finally clauses, which may
# loop and make calls, running before it returns, one after another, and
# then the __del__ of the instances among them. Collections run in
# functions and generators as at module level.
from harness import *

host.disable_automatic_collection()
log = []

def note(entry):
    for _ in range(2): pass
    log.append(entry)

def suspended(name, holder):
    try:
        yield
    finally:
        for _ in range(2): pass
        note(("closed", name))

class Holder:
    def __init__(self, name):
        self.name = name
        self.g = suspended(name, self)
        self.g.gi_frame  # started below
        next(self.g)
    def __del__(self):
        note(("del", self.name))

def collected():
    del log[:]
    for name in ("a", "b"):
        h = Holder(name)
        h.me = h
        del h
    host.collect()
    log.append("after")
    return sorted(e for e in log if e[0] == "closed"), sorted(e for e in log if e[0] == "del"), log[-1]

expected = ([("closed", "a"), ("closed", "b")], [("del", "a"), ("del", "b")], "after")

def gen():
    yield collected()

assert_eq(collected(), expected)
assert_eq(next(gen()), expected)
def main(): return collected()
assert_eq(main(), expected)
