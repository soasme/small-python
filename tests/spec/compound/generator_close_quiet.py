# spec: PLS-315 27.2.1, 27.2.2, 27.2.3
# description: Closing a generator suspended at a yield outside every try,
# with and except, also inside loops, ends it as a GeneratorExit raised
# there would: close() is None, the generator is closed with its frame
# released, and a later next() raises StopIteration; at the recursion
# limit too. A yield inside a with statement, an except
# handler or a yield from still receives the GeneratorExit, the delegate
# closed first, in functions as at module level.
from harness import *

log = []

class Guard:
    def __enter__(self): return self
    def __exit__(self, kind, value, tb):
        log.append(("exit", kind.__name__))

def looping():
    for i in range(3):
        for j in range(2):
            yield i, j

def plain():
    yield 1
    log.append("not reached")

def guarded():
    with Guard():
        yield 1

def handling():
    try:
        raise KeyError("k")
    except KeyError:
        yield 1

def delegating():
    yield from looping()

def states(it):
    return [it.gi_frame is None, it.gi_suspended, list(it)]

def results():
    del log[:]
    out = []
    for make in (looping, plain):
        it = make(); next(it); next(it) if make is looping else None
        out += [it.close(), states(it), it.close()]
    it = guarded(); next(it)
    out.append(it.close())
    it = handling(); next(it)
    try:
        it.close()
    except BaseException as e:
        out.append(type(e).__name__)
    else:
        out.append(None)
    it = delegating(); next(it)
    inner = it.gi_yieldfrom
    out += [it.close(), inner.gi_frame is None, states(it)]
    out.append(list(log))
    return out

expected = [None, [True, False, []], None, None, [True, False, []], None, None, None, None, True, [True, False, []],
            [("exit", "GeneratorExit")]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)

# At the recursion limit a quiet close still succeeds.
it = looping(); next(it)
deep = []
def recurse():
    try:
        recurse()
    except RecursionError:
        if not deep: deep.append(it.close())
recurse()
assert_eq([deep, it.gi_frame], [[None], None])
