# spec: PLS-315 27.2.4, 28.7
# description: generator, coroutine and async_generator each have a
# __del__ slot wrapper that finalizes as reclaiming one does: a suspended
# one closes at its yield, running its finally clauses; one that ends
# again, ignores GeneratorExit, or raises has that exception unraisable,
# and __del__ returns None. Unstarted and closed ones do nothing. Read from the instance, bound, or from the type.
from harness import assert_eq

log = []
def gen(name):
    try:
        for _ in (): pass
        yield 1
    finally:
        log.append(name)
def stubborn():
    try: yield 1
    finally: yield 2
def raises():
    try: yield 1
    finally: raise KeyError("k")
class Await:
    def __await__(self): yield 5
async def co(name):
    try: await Await()
    finally: log.append(name)
async def agen(name):
    try: yield 1
    finally: log.append(name)

def started(g):
    next(g)
    return g
def awaiting(c):
    c.send(None)
    return c
def asent(a):
    try: a.asend(None).send(None)
    except StopIteration: pass
    return a

def run():
    results = []
    for kind, make, step in [("generator", gen, started), ("coroutine", co, awaiting), ("async_generator", agen, asent)]:
        probe = make("x")
        t = type(probe)
        if kind == "coroutine": probe.close()
        results.append((t.__name__, type(t.__dict__["__del__"]).__name__))
        a, b, c = step(make(kind + " a")), step(make(kind + " b")), step(make(kind + " c"))
        results.append((a.__del__(), b.__del__.__self__ is b, (b.__del__)(), t.__del__(c)))
        results.append(a.__del__())
        # (An unstarted coroutine's __del__ also warns that it was never awaited.)
        fresh = make(kind + " fresh")
        if kind == "coroutine": fresh.close()
        results.append(fresh.__del__())
    s, r = started(stubborn()), started(raises())
    results.append((s.__del__(), s.gi_suspended, r.__del__(), r.gi_frame))
    try: gen("y").__del__(1)
    except TypeError as e: results.append(str(e))
    try: type(gen("z")).__del__(1)
    except TypeError as e: results.append(str(e))
    return results

assert_eq(run(), [
    ("generator", "wrapper_descriptor"), (None, True, None, None), None, None,
    ("coroutine", "wrapper_descriptor"), (None, True, None, None), None, None,
    ("async_generator", "wrapper_descriptor"), (None, True, None, None), None, None,
    (None, True, None, None),
    "expected 0 arguments, got 1",
    "descriptor '__del__' requires a 'generator' object but received a 'int'"])
assert_eq(log, ["generator a", "generator b", "generator c", "coroutine a", "coroutine b", "coroutine c",
                "async_generator a", "async_generator b", "async_generator c"])
