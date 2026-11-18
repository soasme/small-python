# spec: PLS-315 13.16.2, 27.5.1, 27.5.2
# description: awaiting athrow() or aclose() of an async generator at a
# yield throws into it there, even at a yield whose value is dropped; its
# handler may await objects whose __await__ is a generator, whose yields
# pass to the driver. A yield ends athrow with that value and aclose with
# RuntimeError; the generator's end gives StopAsyncIteration, or None for
# aclose, as a GeneratorExit escaping it does; another exception
# propagates. An exception class is instantiated, its Python __init__
# called; the exception thrown has no context from the awaiting frame. A
# second await of the awaitable raises RuntimeError.
from harness import *

log = []
class Fut:
    def __init__(self, v): self.v = v
    def __await__(self):
        r = yield self.v
        log.append(("fut", self.v, r))
        return r
async def plain():
    try:
        yield 1
        yield 2
    finally:
        log.append("fin")
        await Fut("f")
async def stubborn():
    try:
        yield 1
    except GeneratorExit:
        yield "again"
async def returns():
    try:
        yield 1
    except BaseException as e:
        log.append(("caught", type(e).__name__))
        await Fut("r")
        return
async def raises():
    try:
        yield 1
    except GeneratorExit:
        raise KeyError("in close")
async def catcher():
    got = "ready"
    while True:
        try:
            yield got
        except ValueError as e:
            log.append(("ve", str(e)))
            await Fut("c")
            got = "handled " + str(e)
class E(Exception):
    def __init__(self, *a):
        log.append(("E.init", a)); super().__init__(*a)
def err(e): return (type(e).__name__, str(e))
async def step(out, name, aw):
    try: out.append((name, await aw))
    except BaseException as e: out.append((name, err(e)))
async def main():
    out = []
    for f in (plain, stubborn, returns, raises):
        a = f(); await a.__anext__()
        await step(out, "close " + f.__name__, a.aclose())
        await step(out, "close again", a.aclose())
    a = catcher(); await a.asend(None)
    await step(out, "ve x", a.athrow(ValueError("x")))
    await step(out, "ve cls", a.athrow(ValueError))
    await step(out, "E cls", a.athrow(E))
    await step(out, "after E", a.asend(None))
    a = catcher(); await a.asend(None)
    await step(out, "E inst", a.athrow(E("y")))
    a = returns(); await a.asend(None)
    await step(out, "returns", a.athrow(KeyError("k")))
    a = plain(); await a.asend(None)
    await step(out, "plain k2", a.athrow(KeyError("k2")))
    await step(out, "plain k3", a.athrow(KeyError("k3")))
    a = plain(); await a.asend(None)
    op = a.aclose()
    await step(out, "op", op)
    await step(out, "op again", op)
    a = catcher(); await a.asend(None)
    try:
        raise IndexError("outer")
    except IndexError:
        try: await a.athrow(KeyError("ctx"))
        except KeyError as e: out.append(("ctx", type(e.__context__).__name__))
    return out
def run(c):
    v = None
    while True:
        try: c.send(v)
        except StopIteration as e: return e.value
        v = "sent"
def go():
    del log[:]
    r = run(main())
    return r, list(log)

expected = ([('close plain', None),
            ('close again', None),
            ('close stubborn', ('RuntimeError', 'async generator ignored GeneratorExit')),
            ('close again', ('StopAsyncIteration', '')),
            ('close returns', None),
            ('close again', None),
            ('close raises', ('KeyError', "'in close'")),
            ('close again', None),
            ('ve x', 'handled x'),
            ('ve cls', 'handled '),
            ('E cls', ('E', '')),
            ('after E', ('StopAsyncIteration', '')),
            ('E inst', ('E', 'y')),
            ('returns', ('StopAsyncIteration', '')),
            ('plain k2', ('KeyError', "'k2'")),
            ('plain k3', None),
            ('op', None),
            ('op again', ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()')),
            ('ctx', 'NoneType')],
            ['fin', ('fut', 'f', 'sent'), ('caught', 'GeneratorExit'), ('fut', 'r', 'sent'), ('ve', 'x'), ('fut', 'c', 'sent'), ('ve', ''), ('fut', 'c', 'sent'), ('E.init', ()), ('E.init', ('y',)), ('caught', 'KeyError'), ('fut', 'r', 'sent'), 'fin', ('fut', 'f', 'sent'), 'fin', ('fut', 'f', 'sent')])

assert_eq(go(), expected)
assert_eq(go(), expected)
