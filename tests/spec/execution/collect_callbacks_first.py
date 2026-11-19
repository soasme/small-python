# spec: PLS-315 9.7
# description: A collection the host asks for calls the callbacks of the
# host's weak references to the unreachable objects it finds, each with its
# reference already cleared, before any of their __del__ methods; a weak
# reference to an object reachable only from one with a __del__ included.
# Then it reclaims what the methods leave unreachable. Inside functions and
# generators as at module level.
from harness import *

host.disable_automatic_collection()
log = []

class Cycle:
    def __init__(self, name):
        self.name, self.me = name, self
    def __del__(self):
        for _ in range(2): pass
        log.append(("del", self.name))

class Bare:
    def __init__(self): self.me = self

def noted(name):
    def callback(ref):
        for _ in range(2): pass
        log.append(("weak", name, ref()))
    return callback

refs = []

def collected():
    del log[:], refs[:]
    a, b = Cycle("a"), Cycle("b")
    held = Bare()
    a.held = held
    refs.extend([host.weak_reference(a, noted("a")), host.weak_reference(held, noted("held")),
                 host.weak_reference(Bare(), noted("bare"))])
    del a, b, held
    host.collect()
    weak = sorted(e for e in log if e[0] == "weak")
    return [sorted(log[:3]), sorted(log[3:]), [r() for r in refs]], weak

def check(result):
    entries, weak = result
    assert_eq(weak, [("weak", "a", None), ("weak", "bare", None), ("weak", "held", None)])
    assert_eq(entries, [weak, [("del", "a"), ("del", "b")], [None, None, None]])

check(collected())
def gen():
    yield collected()
check(next(gen()))
def main(): return collected()
check(main())
