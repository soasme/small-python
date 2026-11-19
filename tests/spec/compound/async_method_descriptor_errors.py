# spec: PLS-315 7.3.2, 7.7.4, 7.7.5, 15.3.2, 19.3.2, 19.3.4
# description: An AttributeError that a descriptor of __aiter__, __anext__
# or __await__ raises as it is read for aiter(), anext(), async for or
# await becomes AttributeError "object T does not have M method", with
# the exception being handled as its context; any other exception of the
# read propagates as it is. A __get__ or a property getter alike, inside
# functions and generators as at module level.
from harness import *

class Get:
    def __init__(self, error): self.error = error
    def __get__(self, obj, cls):
        for _ in range(2): pass
        raise self.error

def failing(error):
    def read(self):
        for _ in range(2): pass
        raise error
    return property(read)

class Missing(AttributeError): pass

def make(name, descriptor):
    async def anext(self): raise StopAsyncIteration
    namespace = {"__aiter__": lambda self: self, "__anext__": anext, "__await__": lambda self: iter(())}
    namespace[name] = descriptor
    return type("T", (), namespace)()

async def over(o):
    async for _ in o: pass

async def awaited(o):
    try:
        raise KeyError("handled")
    except KeyError:
        await o

def drive(coroutine):
    try:
        coroutine.send(None)
    except StopIteration:
        return "ok"
    except Exception as e:
        return (type(e).__name__, str(e), type(e.__context__).__name__ if e.__context__ else None)
    return "suspended"

def builtin(call, o):
    try:
        call(o)
    except Exception as e:
        return (type(e).__name__, str(e), type(e.__context__).__name__ if e.__context__ else None)
    return "ok"

def results():
    out = []
    for make_descriptor in (Get, failing):
        for error in (AttributeError("inner"), Missing("inner"), ValueError("inner")):
            out.append([builtin(aiter, make("__aiter__", make_descriptor(error))),
                        builtin(anext, make("__anext__", make_descriptor(error))),
                        drive(over(make("__aiter__", make_descriptor(error)))),
                        drive(over(make("__anext__", make_descriptor(error)))),
                        drive(awaited(make("__await__", make_descriptor(error))))])
    return out

def absent(name, context=None):
    return ("AttributeError", "object T does not have %s method" % name, context)

replaced = [absent("__aiter__"), absent("__anext__"), absent("__aiter__"), absent("__anext__"), absent("__await__", "KeyError")]
kept = [("ValueError", "inner", None)] * 4 + [("ValueError", "inner", "KeyError")]
expected = [replaced, replaced, kept] * 2

assert_eq(results(), expected)

def inside():
    return results()
assert_eq(inside(), expected)

def gen():
    yield results()
assert_eq(next(gen()), expected)
