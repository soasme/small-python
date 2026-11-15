# spec: PLS-315 26.1.1
# description: dict(), dict.update() and ** of an instance whose keys is
# a function it holds itself merge it as a mapping: that keys called with
# no arguments, then __getitem__ of each key in order; a generator
# function's keys gives its generator's keys. Inside functions as at
# module level.
from harness import *

log = []
class Own:
    def __init__(self, ks):
        def keys():
            for _ in (): pass
            log.append("keys"); return ks
        self.keys = keys
    def __getitem__(self, k):
        for _ in (): pass
        log.append(("get", k)); return k * 2
def gk():
    yield "g"
class Gen:
    def __init__(self): self.keys = gk
    def __getitem__(self, k): return k
def run():
    d = {"z": 0}
    d.update(Own(["a"]))
    return [dict(Own(["b", "c"])), d, {**Own(["e"])}, dict(Gen()), dict(Own([])), log[:]]

expected = [{'b': 'bb', 'c': 'cc'}, {'z': 0, 'a': 'aa'}, {'e': 'ee'}, {'g': 'g'}, {}, ['keys', ('get', 'a'), 'keys', ('get', 'b'), ('get', 'c'), 'keys', ('get', 'e'), 'keys']]
assert_eq(run(), expected)
log.clear()
assert_eq((dict(Own(["m"])), log), ({"m": "mm"}, ["keys", ("get", "m")]))
