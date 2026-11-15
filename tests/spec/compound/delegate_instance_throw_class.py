# spec: PLS-315 13.16.3, 27.2.2
# description: throw() of an exception class into a generator waiting in
# a yield from of an instance, directly or through delegating
# generators, calls the instance's Python throw, which may loop, with
# the class as given, not an instance of it: what it returns is
# throw()'s value, its StopIteration's value ends the yield from, and an
# exception it raises propagates. A GeneratorExit class closes the
# instance and is raised in the generator instead. Inside functions as
# at module level.
from harness import *

log = []

class Delegate:
    def __iter__(self): return self
    def __next__(self): return 1
    def throw(self, *exc):
        for _ in (): pass
        log.append(("throw", exc))
        if exc[0] is KeyError: raise StopIteration(42)
        if exc[0] is IndexError: return "kept"
        raise exc[0]
    def close(self):
        for _ in (): pass
        log.append("close")

def delegate():
    r = yield from Delegate()
    yield ("returned", r)

def outer(): return (yield from delegate())

def throws():
    out = []
    for make in (delegate, outer):
        g = make(); next(g)
        out.append(g.throw(KeyError))
        g = make(); next(g)
        out.append(g.throw(IndexError))
        g.close()
        g = make(); next(g)
        try: g.throw(ValueError)
        except ValueError as e: out.append(repr(e))
        g = make(); next(g)
        try: g.throw(GeneratorExit)
        except GeneratorExit as e: out.append(type(e).__name__)
    return out

expected = [("returned", 42), "kept", "ValueError()", "GeneratorExit"] * 2
expected_log = [("throw", (KeyError,)), ("throw", (IndexError,)), "close", ("throw", (ValueError,)), "close"] * 2
assert_eq(throws(), expected)
assert_eq(log, expected_log)
log.clear()

g = delegate(); next(g)
assert_eq((g.throw(KeyError), log), (("returned", 42), [("throw", (KeyError,))]))
