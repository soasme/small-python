# spec: PLS-315 27.5.1, 27.5
# description: next() and send() of an async generator's __anext__() or
# asend() awaitable resume its generator: a yield ends the send with
# StopIteration holding the yielded value, an await's yield passes out as
# the send's result, the generator's end raises StopAsyncIteration; asend's
# value reaches the yield unless the first send gives another, and an awaitable once ended raises
# RuntimeError when sent again. Inside functions as at module level.
from harness import *

log = []

class Tick:
    def __await__(self):
        for _ in (): pass
        got = yield "tick"
        log.append(("woke", got))

async def agen(n):
    for i in range(n):
        for _ in (): pass
        got = yield i
        log.append(("got", got))
        if got == "pause": await Tick()

def drive(op, value=None, first=None):
    out = []
    try:
        while True:
            out.append(op.send(value) if first is None else next(op))
    except StopIteration as e: out.append(("stop", e.value))
    except StopAsyncIteration: out.append("end")
    return out

def run():
    g = agen(2)
    out = [drive(g.__anext__(), first=1), drive(g.asend("x")), drive(g.asend("pause")), drive(g.__anext__())]
    op = agen(1).__anext__()
    out.append(drive(op))
    try: op.send(None)
    except RuntimeError as e: out.append(str(e))
    return out

expected = [[("stop", 0)], [("stop", 1)], ["tick", "end"], ["end"], [("stop", 0)],
            "cannot reuse already awaited __anext__()/asend()"]
assert_eq(run(), expected)
assert_eq(log, [("got", "x"), ("got", "pause"), ("woke", None)])
log.clear()
assert_eq(drive(agen(3).asend(None)), [("stop", 0)])
