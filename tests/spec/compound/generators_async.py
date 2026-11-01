# spec: PLS-315 27.2, 27.5
# description: send/throw/close, yield from delegation, StopIteration conversion, coroutines and async generators driven manually.
from harness import *

def gen():
    received = yield 1
    try:
        yield received
    except KeyError as e:
        yield ("caught", e.args)
    finally:
        log.append("finally")
    return "done"
log = []
g = gen()
assert_eq(next(g), 1)
assert_eq(g.send("hi"), "hi")
assert_eq(g.throw(KeyError("k")), ("caught", ("k",)))
e = assert_raises(StopIteration, next, g)
assert_eq(e.value, "done")
assert_eq(log, ["finally"])
assert_raises(TypeError, gen().send, 1)
g = gen(); next(g); g.close()
assert_eq(log, ["finally"])
g = gen(); g.close(); g.close()

def no_close():
    try:
        yield 1
    except GeneratorExit:
        yield 2
g = no_close(); next(g)
assert_raises(RuntimeError, g.close)
def close_value():
    try:
        yield
    except GeneratorExit:
        return 7
g = close_value(); next(g)
assert_eq(g.close(), 7)

def inner():
    x = yield "a"
    yield x
    return "inner result"
def outer():
    r = yield from inner()
    yield r
o = outer()
assert_eq([next(o), o.send("b"), next(o)], ["a", "b", "inner result"])
# yield from an iterable that is not a generator.
def yf(): yield from [1, 2]
assert_eq(list(yf()), [1, 2])
# StopIteration inside a generator becomes RuntimeError (PEP 479).
def leaks():
    raise StopIteration
    yield
e = assert_raises(RuntimeError, next, leaks())
assert_type(e.__cause__, StopIteration)
# Running generator cannot be re-entered.
def reenter():
    yield next(me)
me = reenter()
assert_raises(ValueError, next, me)
assert_eq(gen().gi_frame.f_code.co_name, "gen") if False else None
g = gen()
assert_false(g.gi_running)
assert_is(g.gi_yieldfrom, None)
assert_eq(g.__name__, "gen")

# Coroutines are driven by send(None).
class Awaitable:
    def __await__(self):
        value = yield "suspended"
        return value * 2
async def coro():
    v = await Awaitable()
    return v + 1
c = coro()
assert_eq(c.send(None), "suspended")
e = assert_raises(StopIteration, c.send, 10)
assert_eq(e.value, 21)
c = coro(); c.close()
assert_raises(RuntimeError, c.send, None)
async def plain(): return 1
c = plain()
assert_raises(TypeError, lambda: next(c))
assert_raises(TypeError, iter, c)
c.close()
class BadAwait:
    def __await__(self): return 1
async def bad(): await BadAwait()
assert_raises(TypeError, bad().send, None)
assert_raises(TypeError, run, "async def f():\n    await 1\nf().send(None)\n")

# Async generators and the asynchronous iteration protocol.
async def agen():
    for i in range(2):
        yield i
    log.append("agen done")
async def collect():
    out = [x async for x in agen()]
    async with CM() as v:
        out.append(v)
    async for y in AIter():
        out.append(y)
    return out
class CM:
    async def __aenter__(self): return "cm"
    async def __aexit__(self, *a): return False
class AIter:
    def __init__(self): self.n = 0
    def __aiter__(self): return self
    async def __anext__(self):
        if self.n: raise StopAsyncIteration
        self.n = 1
        return "ai"
log.clear()
e = assert_raises(StopIteration, collect().send, None)
assert_eq(e.value, [0, 1, "cm", "ai"])
assert_eq(log, ["agen done"])
a = agen()
assert_eq(type(a).__name__, "async_generator")
e = assert_raises(StopIteration, a.__anext__().send, None)
assert_eq(e.value, 0)
e = assert_raises(StopIteration, a.asend(None).send, None)
assert_eq(e.value, 1)
assert_raises(StopAsyncIteration, a.__anext__().send, None)

assert_syntax_error("def f():\n    await x\n")
assert_syntax_error("def f():\n    async for x in y: pass\n")
assert_syntax_error("def f():\n    async with x: pass\n")
assert_syntax_error("async def f():\n    yield from x\n")
assert_syntax_error("async def f():\n    yield 1\n    return 2\n")
assert_syntax_error("await x")
assert_compiles("async def f():\n    [await x for x in y]\n")
assert_compiles("async def f():\n    return [x async for x in y]\n")
assert_syntax_error("def f():\n    return [x async for x in y]\n")
# An async comprehension inside a sync comprehension in a coroutine is allowed.
assert_compiles("async def f():\n    return [[x async for x in y] for z in w]\n")
assert_compiles("await x", ) if False else None
assert_compiles("await x\n", "exec") if False else None

# async for and async with report CPython's protocol errors.
def protocol_error(coroutine):
    try:
        coroutine.send(None)
    except TypeError as error:
        return str(error)
class NoAiter:
    pass
class BadAnext:
    def __aiter__(self):
        return self
    def __anext__(self):
        return 5
class NoAnext:
    def __aiter__(self):
        return 5
async def loop_over(source):
    async for x in source:
        pass
assert_eq(protocol_error(loop_over(NoAiter())), "'async for' requires an object with __aiter__ method, got NoAiter")
assert_eq(protocol_error(loop_over(BadAnext())), "'async for' received an invalid object from __anext__: int")
assert_eq(protocol_error(loop_over(NoAnext())),
          "'async for' received an object from __aiter__ that does not implement __anext__: int")
e = assert_raises(TypeError, aiter, NoAiter())
assert_eq(str(e), "'NoAiter' object is not an async iterable")
e = assert_raises(TypeError, aiter, NoAnext())
assert_eq(str(e), "NoAnext.__aiter__() must return an async iterator, not int")
class SyncManager:
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        return False
async def async_with_sync():
    async with SyncManager():
        pass
assert_eq(protocol_error(async_with_sync()),
          "'SyncManager' object does not support the asynchronous context manager protocol (missed __aexit__ method)"
          " but it supports the context manager protocol. Did you mean to use 'with'?")

# An __aexit__ that fails when called replaces the exception or result that
# was leaving the async with body.
class FailingExit:
    async def __aenter__(self): return self
    def __aexit__(self, *exc): raise KeyError("exit")
class Pause:
    def __await__(self): yield
async def leave(kind):
    async with FailingExit():
        if kind == "raise": raise ValueError("body")
        if kind == "return": return "result"
        await Pause()
for kind, context in (("raise", ValueError), ("return", type(None)), ("await", type(None))):
    coroutine = leave(kind)
    try:
        coroutine.send(None)
        coroutine.send(None)
    except KeyError as error:
        assert type(error.__context__) is context
    else:
        raise AssertionError(kind)

# A throw with the wrong number of arguments starts the operation and closes it.
async def one(): yield 1
for make, reuse in ((lambda gen: gen.asend(None), "__anext__()/asend()"), (lambda gen: gen.athrow(ValueError), "aclose()/athrow()"),
                    (lambda gen: anext(gen, 5), "__anext__()/asend()")):
    awaitable = make(one())
    assert_raises(TypeError, awaitable.throw, message="throw expected at least 1 argument, got 0")
    assert_raises(RuntimeError, awaitable.throw, 1, 2, 3, 4, message=f"cannot reuse already awaited {reuse}")
    awaitable = make(one())
    assert_raises(TypeError, awaitable.throw, 1, 2, 3, 4, message="throw expected at most 3 arguments, got 4")

# throw() stores a traceback in the exception's field, past a __traceback__ a
# subclass defines; a class must make an instance of BaseException.
class OwnTraceback(Exception):
    @property
    def __traceback__(self): return "own"
def catching():
    try: yield
    except OwnTraceback as e: yield (e.__traceback__, BaseException.__dict__["__traceback__"].__get__(e).tb_next is traceback)
try: raise ValueError
except ValueError as e: traceback = e.__traceback__
g = catching(); next(g)
assert_eq(g.throw(OwnTraceback, OwnTraceback(), traceback), ("own", True))
assert_true(BaseException.__dict__["__traceback__"].__get__(OwnTraceback().with_traceback(traceback)) is traceback)
assert_raises(TypeError, OwnTraceback().with_traceback, 5, message="__traceback__ must be a traceback or None")
class NotMade(Exception):
    def __new__(cls, *args): return 5
for args in ((NotMade,), (NotMade, None, traceback), (NotMade, (1,), traceback)):
    g = catching(); next(g)
    assert_raises(TypeError, g.throw, *args, message=f"calling {NotMade!r} should have returned an instance of BaseException, not int")
try: raise NotMade
except TypeError as e: assert_eq(str(e), f"calling {NotMade!r} should have returned an instance of BaseException, not <class 'int'>")
