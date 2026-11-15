# spec: PLS-315 13.16.2, 27.5.1
# description: send() and throw() of the awaitable of asend() of an async
# generator suspended in an await of an object whose __await__ is a
# generator resume that generator, which may loop: a value sent goes to
# its yield, which the send returns, its return is the await's value, and
# a later yield of the async generator ends the send with StopIteration of
# the value; a thrown exception raises at the __await__ generator's yield,
# or passes out of it to the await. A coroutine awaited in turn alike.
# asend(), athrow() and aclose() while it awaits raise RuntimeError on
# their first send. Inside functions as at module level.
from harness import *

log = []
class Aw:
    def __init__(s, n): s.n = n
    def __await__(s):
        for _ in range(2): pass
        try:
            got = yield ("susp", s.n)
            log.append(("got", got))
            got = yield ("susp2", s.n)
            log.append(("got2", got))
        except KeyError as e:
            log.append(("aw caught", e.args))
            yield "after"
        finally:
            log.append(("aw finally", s.n))
        return s.n * 10
async def co(n):
    return await Aw(n)
async def gen():
    try:
        x = await Aw(1)
        log.append(("x", x))
        y = yield x
        log.append(("y", y))
        z = await co(2)
        yield z
    except ValueError as e:
        log.append(("gen caught", e.args))
        yield "v"
    finally:
        log.append("gen finally")
def step(f):
    for _ in range(2): pass
    try: return ("ok", f())
    except StopIteration as e: return ("stop", e.value)
    except BaseException as e: return (type(e).__name__, str(e))
def run(script):
    del log[:]
    g = gen(); ops = {}
    out = []
    for name, act, arg in script:
        if act == "asend": ops[name] = g.asend(arg); continue
        if act == "athrow": ops[name] = g.athrow(arg); continue
        if act == "aclose": ops[name] = g.aclose(); continue
        op = ops[name]
        out.append(step(lambda: op.send(arg) if act == "send" else op.throw(arg) if act == "throw" else op.close()))
    return out, list(log)
SCRIPTS = [
    [("a", "asend", None), ("a", "send", None), ("a", "send", "s1"), ("a", "send", "s2"), ("b", "asend", "Y"), ("b", "send", None),
     ("b", "send", "t1"), ("b", "send", "t2")],
    [("a", "asend", None), ("a", "send", None), ("a", "throw", KeyError("k")), ("a", "send", None)],
    [("a", "asend", None), ("a", "send", None), ("a", "throw", ValueError("v")), ("a", "send", None)],
    [("a", "asend", None), ("a", "send", None), ("b", "asend", None), ("b", "send", None), ("a", "send", 1)],
    [("a", "asend", None), ("a", "send", None), ("b", "athrow", ValueError("w")), ("b", "send", None), ("a", "send", 1)],
    [("a", "asend", None), ("a", "send", None), ("b", "aclose", None), ("b", "send", None), ("a", "send", 1), ("a", "send", 2)],
    [("a", "asend", None), ("a", "send", None), ("a", "send", 1), ("a", "send", 2), ("b", "asend", None), ("b", "send", None),
     ("b", "throw", KeyError("q")), ("b", "send", None)],
]
EXPECTED = [([('ok', ('susp', 1)), ('ok', ('susp2', 1)), ('stop', 10), ('ok', ('susp', 2)), ('ok', ('susp2', 2)), ('stop', 20)],
  [('got', 's1'), ('got2', 's2'), ('aw finally', 1), ('x', 10), ('y', 'Y'), ('got', 't1'), ('got2', 't2'), ('aw finally', 2)]),
 ([('ok', ('susp', 1)), ('ok', 'after'), ('stop', 10)], [('aw caught', ('k',)), ('aw finally', 1), ('x', 10)]),
 ([('ok', ('susp', 1)), ('stop', 'v'), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()')],
  [('aw finally', 1), ('gen caught', ('v',))]),
 ([('ok', ('susp', 1)), ('RuntimeError', 'anext(): asynchronous generator is already running'), ('ok', ('susp2', 1))],
  [('got', 1)]),
 ([('ok', ('susp', 1)), ('RuntimeError', 'athrow(): asynchronous generator is already running'), ('ok', ('susp2', 1))],
  [('got', 1)]),
 ([('ok', ('susp', 1)),
   ('RuntimeError', 'aclose(): asynchronous generator is already running'),
   ('ok', ('susp2', 1)),
   ('stop', 10)],
  [('got', 1), ('got2', 2), ('aw finally', 1), ('x', 10)]),
 ([('ok', ('susp', 1)), ('ok', ('susp2', 1)), ('stop', 10), ('ok', ('susp', 2)), ('ok', 'after'), ('stop', 20)],
  [('got', 1), ('got2', 2), ('aw finally', 1), ('x', 10), ('y', None), ('aw caught', ('q',)), ('aw finally', 2)])]

def main():
    return [run(s) for s in SCRIPTS]

assert_eq(main(), EXPECTED)
assert_eq([run(s) for s in SCRIPTS], EXPECTED)
