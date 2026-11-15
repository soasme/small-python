# spec: PLS-315 27.5.1, 27.5.2
# description: The first send(None) or __next__() of an athrow() or
# aclose() awaitable, or next() of it, of an async generator suspended at
# a yield throws the athrow's exception, made from its class and value
# first by a Python __init__ that may loop, or GeneratorExit, there: a
# yield after catching it ends athrow with StopIteration of the value and
# aclose with RuntimeError; aclose's generator raising GeneratorExit or
# ending ends it with StopIteration, another exception, StopAsyncIteration
# as RuntimeError, propagating; the operation then ends. Once aclose ran,
# athrow raises StopAsyncIteration without running a generator still
# suspended. Inside functions as at module level.
from harness import *

log = []

class Made(Exception):
    def __init__(self, *args):
        for _ in range(2): pass
        log.append(("init", args))
        super().__init__(*args)

class Exit(GeneratorExit): pass

class BadExit(GeneratorExit):
    def __init__(self, *args): raise KeyError("bad")

async def body(mode):
    try:
        yield 1
    except Made as e:
        yield ("made", e.args)
    except ValueError as e:
        yield ("value", e.args)
    except GeneratorExit as e:
        for _ in range(2): pass
        log.append(("exit", type(e).__name__))
        if mode == "yield": yield "ignored"
        if mode == "raise": raise LookupError("close")
        if mode == "stop": raise StopAsyncIteration
        if mode == "end": return
        raise
    except KeyError as e:
        yield ("key", e.args)

def run(f):
    try:
        return ("value", f())
    except BaseException as e:
        return type(e).__name__, e.args

def started(mode="plain"):
    g = body(mode)
    try:
        next(g.__anext__())
    except StopIteration:
        pass
    return g

def sends():
    del log[:]
    out = []
    for mode in ("plain", "yield", "raise", "stop", "end"):
        g = started(mode)
        op = g.aclose()
        out += [run(lambda: op.send(None)), run(lambda: op.send(None)), run(lambda: g.athrow(ValueError).send(None))]
        if mode == "yield":
            out.append(run(lambda: g.asend(None).send(None)))
    g = started()
    out.append(run(lambda: next(g.athrow(Made, 5))))
    g = started()
    out.append(run(lambda: g.athrow(ValueError, ValueError("v"), None).send(None)))
    g = started()
    out.append(run(lambda: g.athrow(Made, (1, 2)).__next__()))
    g = started()
    out.append(run(lambda: g.athrow(Exit).send(None)))
    g = started()
    out.append(run(lambda: next(g.athrow(BadExit))))
    g = started()
    op = g.athrow(ValueError)
    out += [run(lambda: next(op)), run(lambda: next(op))]
    out.append(run(lambda: g.aclose().send(None)))
    return out + [list(log)]

expected = [("StopIteration", ()), ("RuntimeError", ("cannot reuse already awaited aclose()/athrow()",)), ("StopIteration", ()),
            ("RuntimeError", ("async generator ignored GeneratorExit",)),
            ("RuntimeError", ("cannot reuse already awaited aclose()/athrow()",)), ("StopAsyncIteration", ()), ("GeneratorExit", ()),
            ("LookupError", ("close",)), ("RuntimeError", ("cannot reuse already awaited aclose()/athrow()",)), ("StopIteration", ()),
            ("RuntimeError", ("async generator raised StopAsyncIteration",)),
            ("RuntimeError", ("cannot reuse already awaited aclose()/athrow()",)), ("StopIteration", ()), ("StopIteration", ()),
            ("RuntimeError", ("cannot reuse already awaited aclose()/athrow()",)), ("StopIteration", ()),
            ("StopIteration", (("made", (5,)),)), ("StopIteration", (("value", ("v",)),)), ("StopIteration", (("made", (1, 2)),)),
            ("Exit", ()), ("StopIteration", (("key", ("bad",)),)), ("StopIteration", (("value", ()),)),
            ("RuntimeError", ("cannot reuse already awaited aclose()/athrow()",)), ("StopIteration", ()),
            [("exit", "GeneratorExit"), ("exit", "GeneratorExit"), ("exit", "GeneratorExit"), ("exit", "GeneratorExit"),
             ("exit", "GeneratorExit"), ("init", (5,)), ("init", (1, 2)), ("exit", "Exit")]]

def main():
    return sends()

assert_eq(main(), expected)
assert_eq(sends(), expected)
