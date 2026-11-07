# spec: PLS-315 27.2.1, 27.2.2
# description: A generator's close() resumes it at its yield with a new
# GeneratorExit: a handler's return value is close()'s, re-raising or
# finishing gives None, a yield is a RuntimeError, any other exception
# propagates and a StopIteration becomes a RuntimeError; a created or closed
# generator's close() is None. Handlers that loop run in function
# statements as at module level, and a close that fails for recursion
# leaves a generator that closes later.
from harness import *

log = []

def g(kind):
    try:
        x = yield 1
        log.append(("sent", x))
        yield 2
    except GeneratorExit as e:
        for _ in range(2): pass
        log.append(("exit", kind, type(e).__name__))
        if kind == "ignore": yield 3
        if kind == "return": return 7
        if kind == "raise": raise KeyError("k")
        if kind == "stop": raise StopIteration
        if kind == "finish": return
        raise
    finally:
        log.append(("finally", kind))

def plain():
    try:
        yield 1
    finally:
        for _ in range(2): pass
        log.append("plain")

def closes():
    del log[:]
    out = []
    for kind in ("reraise", "return", "ignore", "raise", "stop", "finish"):
        it = g(kind); next(it)
        try: out.append(it.close())
        except Exception as e: out.append((type(e).__name__, str(e)))
    it = plain(); next(it)
    out += [it.close(), it.close(), g("created").close()]
    it = g("return"); next(it); it.send("v")
    close = it.close
    out.append(close())
    out.append(list(log))
    return out

expected = [None, 7, ("RuntimeError", "generator ignored GeneratorExit"), ("KeyError", "'k'"),
            ("RuntimeError", "generator raised StopIteration"), None, None, None, None, 7,
            [("exit", "reraise", "GeneratorExit"), ("finally", "reraise"),
             ("exit", "return", "GeneratorExit"), ("finally", "return"),
             ("exit", "ignore", "GeneratorExit"),
             ("exit", "raise", "GeneratorExit"), ("finally", "raise"),
             ("exit", "stop", "GeneratorExit"), ("finally", "stop"),
             ("exit", "finish", "GeneratorExit"), ("finally", "finish"),
             "plain", ("sent", "v"), ("exit", "return", "GeneratorExit"), ("finally", "return")]]
# The ignoring generator closes again when released; compare up to there.
assert_eq(closes()[:10], expected[:10])
assert_eq(closes()[-1][:5], expected[-1][:5])

it = plain(); next(it)
assert_eq([it.close(), log[-1]], [None, "plain"])

# A close at the recursion limit may fail; the generator still closes.
it = plain(); next(it)
deep = []
def recurse():
    try:
        recurse()
    except RecursionError:
        if not deep:
            try: deep.append(it.close())
            except RecursionError: deep.append("recursion")
del log[:]
recurse()
assert_eq([deep[0] in (None, "recursion"), it.close(), it.close()], [True, None, None])
