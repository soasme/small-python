# spec: PLS-315 9.7
# description: A collection the host asks for reclaims only the objects
# that were unreachable when it began: a cycle that a __del__ method or a
# weak reference callback it calls makes, or one that becomes unreachable
# when such a method drops its last reference, waits for the next
# collection, its __del__ and callbacks with it. Inside functions and
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

refs = []

def noted(name):
    return lambda ref: log.append(("weak", name))

def bare(name):
    b = Bare()
    refs.append(host.weak_reference(b, noted(name)))
    return b

kept = None

class Maker:
    def __init__(self): self.me = self
    def __del__(self):
        global kept
        log.append(("del", "maker"))
        Cycle("made")
        bare("made")
        kept = None

def callback(ref):
    log.append(("weak", "maker"))
    Cycle("called")

def collections():
    global kept
    del log[:], refs[:]
    kept = Cycle("kept")
    maker = Maker()
    refs.append(host.weak_reference(maker, callback))
    del maker
    rounds = []
    for _ in range(3):
        host.collect()
        rounds.append(sorted(log))
        del log[:]
    return rounds

expected = [[("del", "maker"), ("weak", "maker")],
            [("del", "called"), ("del", "kept"), ("del", "made"), ("weak", "made")],
            []]

assert_eq(collections(), expected)
def gen():
    yield collections()
assert_eq(next(gen()), expected)
def main(): return collections()
assert_eq(main(), expected)
