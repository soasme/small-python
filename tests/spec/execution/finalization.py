# spec: PLS-315 9.7, B.4.3
# description: __del__ runs at most once; cycles are reclaimed; exceptions from __del__ do not propagate.
from harness import *

log = []
class Finalized:
    def __init__(self, name):
        self.name = name
    def __del__(self):
        log.append(self.name)

def make():
    Finalized("local")
make()
host.collect()
assert_eq(log, ["local"])

# Objects reachable only through a cycle are reclaimed, with their __del__.
log.clear()
a, b = Finalized("a"), Finalized("b")
a.other, b.other = b, a
del a, b
host.collect()
assert_eq(sorted(log), ["a", "b"])

# __del__ runs at most once, even when it resurrects the object.
saved = []
class Phoenix:
    def __del__(self):
        log.append("phoenix")
        saved.append(self)
log.clear()
Phoenix()
host.collect()
assert_eq(log, ["phoenix"])
saved.clear()
host.collect()
assert_eq(log, ["phoenix"])

# An exception escaping __del__ is not propagated.
class Raises:
    def __del__(self):
        log.append("raised")
        raise RuntimeError("ignored")
log.clear()
Raises()
host.collect()
assert_eq(log, ["raised"])
