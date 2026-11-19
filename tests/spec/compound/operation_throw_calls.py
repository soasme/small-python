# spec: PLS-315 27.5.1, 27.4.2, 13.4.2
# description: throw() into a coroutine suspended in an await of an async
# generator's asend() or athrow() awaitable, whose generator is suspended
# in an await of its own, raises the exception there: the generator may
# handle it and yield, which ends the await with that value; return or run
# off its end, which raises StopAsyncIteration (an athrow() gives None);
# await again, which suspends the coroutine; or let it propagate, ending
# the generator. A class is instantiated. Inside functions as at module
# level.
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

def main():
    return results()

assert_eq(main(), expected)
