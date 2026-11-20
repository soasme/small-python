# spec: PLS-315 24.4.2, 9.7
# description: a view that dies unreleased, its last reference dropped or
# its cycle collected, calls its exporter's Python __release_buffer__ once
# with the view it exported, before the next statement runs; an exception
# that call raises is unraisable and the program goes on. Inside
# functions, generators and at module level.
from harness import *

log = []
class Exporter:
    def __init__(self, fails=False): self.fails = fails
    def __buffer__(self, flags):
        log.append("get")
        return memoryview(b"ab")
    def __release_buffer__(self, view):
        log.append(("release", view.tobytes()))
        if self.fails: raise KeyError("release")

def dropped(fails):
    m = memoryview(Exporter(fails))
    del m
    log.append("after")
    return log.pop(0), log.pop(0), log.pop(0)
for fails in (False, True):
    assert_eq(dropped(fails), ("get", ("release", b"ab"), "after"))
    assert_eq(log, [])

m = memoryview(Exporter())
m = None
log.append("after")
assert_eq(log, ["get", ("release", b"ab"), "after"])
log.clear()

def made():
    yield memoryview(Exporter(True))
    log.append("resumed")
for v in made():
    assert_eq(v[0], 97)
    del v
    log.append("after")
assert_eq(log, ["get", ("release", b"ab"), "after", "resumed"])
log.clear()

host.disable_automatic_collection()
def cycle(fails):
    ring = [memoryview(Exporter(fails))]
    ring.append(ring)
    del ring
    assert_eq(log, ["get"])
    host.collect()
    log.append("after")
for fails in (False, True):
    cycle(fails)
    assert_eq(log, ["get", ("release", b"ab"), "after"])
    log.clear()
views = [memoryview(Exporter()) for _ in range(3)]
views.append(views)
del views
host.collect()
assert_eq(log, ["get"] * 3 + [("release", b"ab")] * 3)
