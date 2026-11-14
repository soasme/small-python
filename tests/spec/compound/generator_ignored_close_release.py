# spec: PLS-315 27.2.4, 9.7
# description: a generator or coroutine that, closed when unreachable,
# ignores the GeneratorExit and suspends again inside its handler, in a
# yield from or await, is reclaimed afterwards: its locals are finalized
# and the iterator it delegates to is closed, each time and not only the
# first, though the handled exception's traceback refers to its frame.
from harness import *

log = []

class Del:
    def __init__(self, n): self.n = n
    def __del__(self): log.append(("del", self.n))

def inner(n):
    try:
        yield "inner"
    finally:
        log.append(("inner closed", n))

def stubborn(n):
    d = Del(n)
    try:
        yield 1
    except GeneratorExit:
        log.append(("ignored", n))
        yield from inner(n)

class Ready:
    def __init__(self, n): self.n = n
    def __await__(self):
        try:
            yield "ready"
        finally:
            log.append(("ready closed", self.n))

async def stubborn_coroutine(n):
    d = Del(n)
    try:
        await Ready(n)
    except GeneratorExit:
        log.append(("ignored", n))
        await Ready(n + 10)

def drop(n):
    g = stubborn(n)
    next(g)
    del g
    log.append(("dropped", n))

def drop_coroutine(n):
    c = stubborn_coroutine(n)
    c.send(None)
    c = None
    log.append(("dropped", n))

for n in (1, 2, 3):
    drop(n)
for n in (4, 5):
    drop_coroutine(n)
assert_eq(log, [("ignored", 1), ("inner closed", 1), ("del", 1), ("dropped", 1),
                ("ignored", 2), ("inner closed", 2), ("del", 2), ("dropped", 2),
                ("ignored", 3), ("inner closed", 3), ("del", 3), ("dropped", 3),
                ("ready closed", 4), ("ignored", 4), ("ready closed", 14), ("del", 4), ("dropped", 4),
                ("ready closed", 5), ("ignored", 5), ("ready closed", 15), ("del", 5), ("dropped", 5)])
