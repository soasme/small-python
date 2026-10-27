# spec: reference/datamodel.html#with-statement-context-managers
# description: __enter__/__exit__ protocol and the with statement expansion.
from harness import *

log = []
class CM:
    def __init__(self, name, suppress=False):
        self.name, self.suppress = name, suppress
    def __enter__(self):
        log.append(("enter", self.name))
        return self.name
    def __exit__(self, typ, value, tb):
        log.append(("exit", self.name, typ))
        return self.suppress

with CM("a") as a, CM("b") as b:
    log.append((a, b))
assert_eq(log, [("enter", "a"), ("enter", "b"), ("a", "b"), ("exit", "b", None), ("exit", "a", None)])

log.clear()
with CM("s", suppress=True):
    raise ValueError
assert_eq(log[-1], ("exit", "s", ValueError))

log.clear()
def f():
    with CM("r"):
        return "ret"
assert_eq(f(), "ret")
assert_eq(log, [("enter", "r"), ("exit", "r", None)])

# Parenthesized multi-item with.
with (CM("p") as p,
      CM("q") as q,):
    pass
assert_eq((p, q), ("p", "q"))

# __enter__ is looked up on the type, before the body runs.
class Missing: pass
assert_raises(TypeError, run, "with Missing(): pass", {"Missing": Missing})
class OnlyEnter:
    def __enter__(self): pass
e = assert_raises(TypeError, run, "with OnlyEnter(): pass", {"OnlyEnter": OnlyEnter})
class Inst:
    pass
i = Inst()
i.__enter__ = lambda: 1
i.__exit__ = lambda *a: None
assert_raises(TypeError, run, "with i: pass", {"i": i})

# An exception from __exit__ replaces the original, with context.
class Raising:
    def __enter__(self): return self
    def __exit__(self, *a): raise KeyError("exit")
try:
    with Raising():
        raise ValueError("body")
except KeyError as err:
    assert_type(err.__context__, ValueError)

# The target is assigned after __enter__; unpacking targets work.
class Pair:
    def __enter__(self): return (1, 2)
    def __exit__(self, *a): pass
with Pair() as (x, y):
    pass
assert_eq((x, y), (1, 2))
# break and continue run __exit__.
log.clear()
for _ in range(2):
    with CM("loop"):
        continue
assert_eq(len(log), 4)
