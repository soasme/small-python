# spec: PLS-315 9.7
# description: An explicit collection of unreachable cycles calls their
# Python __del__ methods, which may loop, and the Python callbacks of weak
# references to them, all before it returns.
# Collections run in functions and generators as at module level.
from harness import *

host.disable_automatic_collection()
log = []

class Cycle:
    def __init__(self, name):
        self.name, self.me = name, self
    def __del__(self):
        for _ in range(2): pass
        log.append(("del", self.name))

def noted(name):
    def callback(ref):
        for _ in range(2): pass
        log.append(("weak", name))
    return callback

class Bare:
    def __init__(self): self.me = self

def collected():
    del log[:]
    refs = []
    for name in ("a", "b"):
        c = Cycle(name)
        del c
        b = Bare()
        refs.append(host.weak_reference(b, noted(name)))
        del b
    host.collect()
    log.append("after")
    return sorted(log[:-1]) + log[-1:], [r() for r in refs]

expected = [("del", "a"), ("del", "b"), ("weak", "a"), ("weak", "b"), "after"]

def check(result):
    entries, refs = result
    assert_eq(entries, expected)
    assert_eq(refs, [None, None])

def gen():
    yield collected()

check(collected())
check(next(gen()))
def main(): return collected()
check(main())
