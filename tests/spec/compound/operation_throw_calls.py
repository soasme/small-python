# spec: PLS-315 27.5.1, 27.4.2, 13.4.2
# description: throw() into a coroutine suspended in an await of an async
# generator's asend() or athrow() awaitable, whose generator is suspended
# in an await of its own, raises the exception there: the generator may
# handle it and yield, which ends the await with that value; return or run
# off its end, which raises StopAsyncIteration (an athrow() gives None);
# await again, which suspends the coroutine; or let it propagate, ending
# the generator. A class is instantiated. close(), or a throw of
# GeneratorExit, closes the awaitable first, throwing GeneratorExit into
# the generator: a value it yields, its return or a GeneratorExit or
# StopAsyncIteration it raises then raise GeneratorExit in the coroutine,
# a thrown one itself; an await it suspends in raises RuntimeError, as a
# value an aclose()'s generator yields does; another exception raises in
# the coroutine. Inside functions as at module level.
from harness import *

log = []

class Pause:
    def __init__(self, v): self.v = v
    def __await__(self):
        return (yield self.v)

async def body(after):
    try:
        await Pause("p")
    except KeyError as e:
        for _ in range(2): pass
        log.append(("caught", type(e).__name__, e.args))
        if after == "yield": yield "handled"
        elif after == "await": yield await Pause("again")
        elif after == "return": return
    finally:
        log.append("finally")
    yield "end"

async def next_of(g):
    return await anext(g)

async def thrown_of(g):
    return await g.athrow(ValueError)

def step(co, how):
    try:
        return ("suspended", co.throw(*how))
    except StopIteration as e:
        return ("value", e.value)
    except BaseException as e:
        return ("raised", type(e).__name__)

def run(after, how=(KeyError("k"),), wrap=next_of):
    del log[:]
    g = body(after)
    co = wrap(g)
    first = co.send(None)
    out = [first, step(co, how)]
    if out[-1][0] == "suspended":
        try: co.send("sent")
        except StopIteration as e: out.append(("value", e.value))
    return out, log[:]

async def thrower():
    try:
        yield 1
    except ValueError:
        try:
            await Pause("in athrow")
        except KeyError as e:
            log.append(("athrow caught", e.args))
            yield "from athrow"

def athrown(how):
    del log[:]
    g = thrower()
    first = g.asend(None)
    try: first.send(None)
    except StopIteration as e: log.append(("first", e.value))
    co = thrown_of(g)
    return [co.send(None), step(co, how)], log[:]

async def exiting(after):
    try:
        await Pause("p")
    except GeneratorExit:
        for _ in range(2): pass
        log.append("exit")
        if after == "yield": yield "kept"
        elif after == "await": await Pause("again")
        elif after == "raise": raise KeyError("k")
        elif after == "return": return
        raise
    yield "end"

async def closer():
    try:
        yield 1
    except GeneratorExit:
        try:
            await Pause("in aclose")
        except GeneratorExit:
            log.append("closing")
            yield "late"

async def closed_of(g):
    return await g.aclose()

def started():
    g = closer()
    try: g.asend(None).send(None)
    except StopIteration: pass
    return g

def closing(g, wrap, how):
    del log[:]
    co = wrap(g)
    first = co.send(None)
    try:
        out = ("returned", co.close() if how == "close" else co.throw(GeneratorExit("mine")))
    except BaseException as e:
        out = (type(e).__name__, str(e), type(e.__context__).__name__)
    return first, out, log[:]

def closes():
    return [closing(exiting(after), next_of, how) for after in ("yield", "await", "raise", "return", "reraise")
            for how in ("close", "throw")] + [closing(started(), closed_of, how) for how in ("close", "throw")]

closed = [
    ("p", ("returned", None), ["exit"]), ("p", ("GeneratorExit", "mine", "NoneType"), ["exit"]),
    ("p", ("RuntimeError", "coroutine ignored GeneratorExit", "NoneType"), ["exit"]),
    ("p", ("RuntimeError", "coroutine ignored GeneratorExit", "NoneType"), ["exit"]),
    ("p", ("KeyError", "'k'", "GeneratorExit"), ["exit"]), ("p", ("KeyError", "'k'", "GeneratorExit"), ["exit"]),
    ("p", ("returned", None), ["exit"]), ("p", ("GeneratorExit", "mine", "NoneType"), ["exit"]),
    ("p", ("returned", None), ["exit"]), ("p", ("GeneratorExit", "mine", "NoneType"), ["exit"]),
    ("in aclose", ("RuntimeError", "async generator ignored GeneratorExit", "NoneType"), ["closing"]),
    ("in aclose", ("RuntimeError", "async generator ignored GeneratorExit", "NoneType"), ["closing"]),
]

def results():
    return [run("yield"), run("await"), run("return"), run("raise"), run("yield", (KeyError,)),
            run("raise", (ValueError("v"),)), athrown((KeyError("a"),)), athrown((LookupError,))]

expected = [
    (["p", ("value", "handled")], [("caught", "KeyError", ("k",))]),
    (["p", ("suspended", "again"), ("value", "sent")], [("caught", "KeyError", ("k",))]),
    (["p", ("raised", "StopAsyncIteration")], [("caught", "KeyError", ("k",)), "finally"]),
    (["p", ("value", "end")], [("caught", "KeyError", ("k",)), "finally"]),
    (["p", ("value", "handled")], [("caught", "KeyError", ())]),
    (["p", ("raised", "ValueError")], ["finally"]),
    (["in athrow", ("value", "from athrow")], [("first", 1), ("athrow caught", ("a",))]),
    (["in athrow", ("raised", "LookupError")], [("first", 1)]),
]

assert_eq(results(), expected)
assert_eq(closes(), closed)

def main():
    return results(), closes()

assert_eq(main(), (expected, closed))
