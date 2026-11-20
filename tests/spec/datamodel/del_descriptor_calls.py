# spec: PLS-315 10.3, 7.3.2, 18.1.4
# description: An instance whose class's __del__ is a descriptor is
# finalized by reading it through its getter, then calling what the read
# gave with no arguments, once, when its last reference goes or the
# collector frees its cycle. An error of the read, AttributeError or
# another, is dropped and nothing is called; an error of the call is
# unraisable. Neither reaches the code that dropped the instance.
from harness import *

log = []
def booh(self): raise AttributeError("booh")
def boom(self): raise KeyError("boom")
def gives(tag, fail):
    def get(self):
        for _ in (): pass
        log.append(("get", tag))
        def finalize():
            log.append(("del", tag))
            if fail: raise ValueError("in del")
        return finalize
    return property(get)

class Reads:
    def __get__(self, obj, owner):
        log.append(("Reads", type(obj).__name__))
        return lambda: log.append(("del", "R"))

A = type("A", (), {"__del__": property(booh)})
B = type("B", (), {"__del__": property(boom)})
C = type("C", (), {"__del__": gives("C", 0)})
E = type("E", (), {"__del__": gives("E", 1)})
R = type("R", (), {"__del__": Reads()})

def drop():
    for _ in (): pass
    del log[:]
    A(); B(); C(); E(); R()
    x = C()
    x = None
    log.append("dropped")
    return list(log)

def cycle():
    for _ in (): pass
    del log[:]
    c = C(); c.me = c
    e = E(); e.me = e
    del c, e
    host.collect()
    # The collector finalizes a cycle's instances in no stated order.
    return sorted(log, key=repr)

expected = [("get", "C"), ("del", "C"), ("get", "E"), ("del", "E"), ("Reads", "R"), ("del", "R"),
            ("get", "C"), ("del", "C"), "dropped"]
assert_eq(drop(), expected)
assert_eq(drop(), expected)
assert_eq(cycle(), sorted([("get", "C"), ("del", "C"), ("get", "E"), ("del", "E")], key=repr))
