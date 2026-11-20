# spec: PLS-315 27.1.6, 27.2.2, 27.4.2
# description: map() of a generator's or coroutine's own method, send,
# throw or close taken from its type, resumes each generator with the
# map's next items as that method called directly does: what it yields is
# the item, a throw's exception it does not handle propagates out of the
# map, and close runs its cleanup, a coroutine's handler of GeneratorExit
# too, giving what it returns.
from harness import *

log = []
def gen(tag):
    try:
        x = yield tag
        log.append(("sent", tag, x))
        yield x
    finally:
        for _ in (): pass
        log.append(("fin", tag))

class Y:
    def __await__(self):
        yield "y"

async def co():
    try:
        await Y()
    except GeneratorExit:
        log.append("co exit")
        return "closed"

def started(g):
    for _ in (): pass
    g.send(None)
    return g

def results():
    del log[:]
    gs = [gen(1), gen(2)]
    out = [list(map(next, gs)), list(map(type(gs[0]).send, gs, ["a", "b"])),
           list(map(type(gs[0]).close, [started(gen(3))]))]
    try: out.append(list(map(type(gs[0]).throw, [started(gen(4))], [KeyError("k")])))
    except KeyError as e: out.append(("KeyError", str(e)))
    c = started(co())
    out.append(list(map(type(c).close, [c])))
    out.append(list(map(type(gs[0]).send, [started(gen(5))], [6])))
    return out, list(log)

expected = ([[1, 2], ["a", "b"], [None], ("KeyError", "'k'"), ["closed"], [6]],
            [("sent", 1, "a"), ("sent", 2, "b"), ("fin", 3), ("fin", 4), "co exit", ("sent", 5, 6), ("fin", 5)])

assert_eq(results(), expected)
assert_eq(results(), expected)
