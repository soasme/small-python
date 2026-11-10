# spec: PLS-315 13.16.3, 27.2.2, 13.4
# description: A generator suspended in a yield from, or a coroutine in an
# await, passes throw()'s arguments on as given: an iterator instance's
# throw receives them unchecked, and the generator the throw reaches
# checks them, its TypeError raising at each yield from it passes, which
# may handle it, the innermost generator left suspended. A delegate with
# no throw, or a GeneratorExit closing the delegate, has the delegating
# generator check them: a TypeError then leaves it suspended, inside
# functions as at module level.
from harness import *

log = []

class It:
    def __iter__(self): return self
    def __next__(self): return 1
    def throw(self, *args):
        log.append(("throw", args))
        return "thrown"
    def close(self):
        log.append("close")

class Bare:
    def __iter__(self): return self
    def __next__(self): return 1

def inner():
    try:
        yield 1
    finally:
        log.append("inner done")

def deleg(it):
    try:
        yield from it
    except TypeError as e:
        log.append(("caught", str(e)[:24]))
        yield "caught"

def outer(it):
    try:
        yield from deleg(it)
    except TypeError as e:
        log.append(("outer caught", str(e)[:24]))
        yield "outer"

class Awaited:
    def __await__(self):
        return (yield from inner())

async def awaiting(awaitable):
    try:
        return await awaitable
    except TypeError as e:
        log.append(("awaiting caught", str(e)[:24]))
        return "awaiting"

def run(g, *args):
    g.send(None)
    try:
        r = g.throw(*args)
    except BaseException as e:
        r = (type(e).__name__, str(e)[:24])
    alive = (g.gi_frame if hasattr(g, "gi_frame") else g.cr_frame) is not None
    out = (r, alive, list(log))
    del log[:]
    return out

def results():
    del log[:]
    return [run(deleg(It()), 1), run(deleg(Bare()), 1), run(outer(Bare()), 1),
            run(deleg(inner()), GeneratorExit, 1, 2), run(outer(inner()), GeneratorExit, 1, 2),
            run(deleg(It()), GeneratorExit, 1, 2), run(deleg(Bare()), KeyError, 1, 2),
            run(outer(It()), KeyError), run(awaiting(Awaited()), 1), run(outer(inner()), 1),
            run(deleg(inner()), KeyError("k"), 1)]

message = "exceptions must be class"
expected = [("thrown", True, [("throw", (1,))]),
            (("TypeError", message), True, ["close"]),
            ("outer", True, [("outer caught", message)]),
            (("TypeError", "throw() third argument m"), True, ["inner done"]),
            (("TypeError", "throw() third argument m"), True, ["inner done"]),
            (("TypeError", "throw() third argument m"), True, ["close"]),
            (("TypeError", "throw() third argument m"), True, ["close"]),
            ("thrown", True, [("throw", (KeyError,))]),
            (("StopIteration", "awaiting"), False, ["close", "inner done", ("awaiting caught", message)]),
            ("caught", True, [("caught", message)]),
            ("caught", True, ["inner done", ("caught", "instance exception may n")])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
