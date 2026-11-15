# spec: PLS-315 13.16.2, 27.5.1
# description: throw() of an exception, a class or a class and its value
# into the awaitable of __anext__() or asend() of an async generator
# suspended at a yield raises it there: a yield after catching it ends the
# throw with StopIteration of the value, a return with
# StopAsyncIteration, an uncaught exception propagates, ending the
# generator, and the StopIteration an async generator raises becomes
# RuntimeError; the handler may loop. A class whose __init__ raises
# throws that exception instead. The operation then ends: its send raises
# RuntimeError. Inside functions as at module level.
from harness import *

log = []

async def values():
    while True:
        try:
            sent = yield "ready"
            log.append(("sent", sent))
        except ValueError as e:
            for _ in range(2): pass
            log.append(("caught", str(e)))
            yield "caught " + str(e)
        except KeyError:
            log.append("returning")
            return
        except LookupError:
            raise StopIteration("inner")

class Made(Exception):
    def __init__(self, *args):
        for _ in range(2): pass
        raise KeyError("made")

def outcome(f):
    try:
        return ("value", f())
    except BaseException as e:
        return type(e).__name__, e.args, type(e.__cause__).__name__

def run():
    del log[:]
    g = values()
    out = [outcome(lambda: next(g.__anext__()))]
    op = g.__anext__()
    out.append(outcome(lambda: op.throw(ValueError("one"))))
    out.append(outcome(lambda: op.send(None)))
    out.append(outcome(lambda: g.asend("x").send(None)))
    out.append(outcome(lambda: g.asend(None).throw(ValueError, "two")))
    out.append(outcome(lambda: g.asend(None).throw(ValueError)))
    out.append(outcome(lambda: g.asend(None).send(None)))
    out.append(outcome(lambda: g.asend(None).throw(TypeError("three"))))
    out.append(outcome(lambda: g.__anext__().send(None)))
    h = values()
    out.append(outcome(lambda: next(h.__anext__())))
    out.append(outcome(lambda: h.__anext__().throw(KeyError)))
    k = values()
    out.append(outcome(lambda: next(k.__anext__())))
    out.append(outcome(lambda: k.__anext__().throw(IndexError("i"))))
    m = values()
    out.append(outcome(lambda: next(m.__anext__())))
    out.append(outcome(lambda: m.__anext__().throw(Made)))
    return out + [g.ag_running, h.ag_running, list(log)]

expected = [("StopIteration", ("ready",), "NoneType"), ("StopIteration", ("caught one",), "NoneType"),
            ("RuntimeError", ("cannot reuse already awaited __anext__()/asend()",), "NoneType"),
            ("StopIteration", ("ready",), "NoneType"), ("StopIteration", ("caught two",), "NoneType"),
            ("ValueError", (), "NoneType"), ("StopAsyncIteration", (), "NoneType"), ("TypeError", ("three",), "NoneType"),
            ("StopAsyncIteration", (), "NoneType"), ("StopIteration", ("ready",), "NoneType"), ("StopAsyncIteration", (), "NoneType"),
            ("StopIteration", ("ready",), "NoneType"), ("RuntimeError", ("async generator raised StopIteration",), "StopIteration"),
            ("StopIteration", ("ready",), "NoneType"), ("StopAsyncIteration", (), "NoneType"),
            False, False, [("caught", "one"), ("caught", "two"), "returning", "returning"]]

def main():
    return run()

assert_eq(main(), expected)
assert_eq(run(), expected)
