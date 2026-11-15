# spec: PLS-315 13.16.3, 27.2.2
# description: throw() of an exception instance into a generator waiting
# in a yield from of a builtin iterator, which has no throw method,
# raises it in the generator at the yield from, whose handler, which may
# loop, may yield; an unhandled one propagates and finishes the
# generator. close() raises GeneratorExit there, running its finally
# clauses. Lists, tuple iterators, maps and ranges; inside functions as
# at module level.
from harness import *

log = []

def gen(source):
    try:
        yield "a"
        r = yield from source
        log.append(("r", r))
    except KeyError as e:
        for _ in (): pass
        log.append(("caught", e.args))
        yield "handled"
    finally:
        log.append("finally")

def throws():
    out = []
    for source in (lambda: [1, 2], lambda: iter((3, 4)), lambda: map(str, [5, 6]), lambda: range(2)):
        g = gen(source()); next(g); out.append(next(g))
        out.append(g.throw(KeyError("k")))
        g.close()
        g = gen(source()); next(g); next(g)
        out.append(g.close())
        g = gen(source()); next(g); next(g)
        try: g.throw(ValueError("v"))
        except ValueError as e: out.append(e.args)
        out.append(g.gi_frame is None)
    return out

expected = [1, "handled", None, ("v",), True, 3, "handled", None, ("v",), True, "5", "handled", None, ("v",), True,
            0, "handled", None, ("v",), True]
expected_log = [("caught", ("k",)), "finally", "finally", "finally"] * 4
assert_eq(throws(), expected)
assert_eq(log, expected_log)
log.clear()
assert_eq(throws(), expected)
assert_eq(log, expected_log)
