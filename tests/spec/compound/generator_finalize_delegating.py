# spec: PLS-315 27.2.4, 27.2.3, 13.16.3
# description: a suspended generator whose last reference goes while it
# waits in a yield from is closed before the next statement runs: a
# delegate generator, or an instance's Python close, is closed first,
# then the delegator's finally clauses, which may loop, run; a builtin
# iterator delegate has no close. An error the close raises is
# unraisable and leaves the program going. Inside functions as at module
# level.
from harness import *

log = []

class It:
    def __iter__(self): return self
    def __next__(self): return 1
    def close(self):
        for _ in (): pass
        log.append("it close")

class Failing(It):
    def close(self):
        for _ in (): pass
        raise KeyError("close")

def gen(source, tag):
    try:
        yield from source
    finally:
        for _ in (): pass
        log.append(("finally", tag))

def run():
    for tag, source in (("list", lambda: [1, 2]), ("it", It), ("map", lambda: map(str, [1, 2])), ("tuple", lambda: iter((1, 2)))):
        g = gen(source(), tag); next(g)
        del g
        log.append("dropped")
    g = gen(gen([1, 2], "inner"), "outer"); next(g)
    g = None
    log.append("nested")
    g = gen(Failing(), "failing"); next(g)
    del g
    log.append("survived")

expected = [("finally", "list"), "dropped", "it close", ("finally", "it"), "dropped", ("finally", "map"), "dropped",
            ("finally", "tuple"), "dropped", ("finally", "inner"), ("finally", "outer"), "nested", ("finally", "failing"),
            "survived"]
run()
assert_eq(log, expected)
log.clear()

g = gen(It(), "module"); next(g)
del g
log.append("after")
assert_eq(log, ["it close", ("finally", "module"), "after"])
