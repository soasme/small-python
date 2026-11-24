# spec: PLS-315 7.4.1, 19.3.2, 13.4, 15.3.2
# description: Awaiting a class, or iterating one by async for or an
# asynchronous comprehension, calls its metaclass's __await__ or
# __aiter__, a Python method or a descriptor whose Python __get__ is read
# first, either of which may loop, with the class; a read's AttributeError
# means the metaclass lacks the method, and other exceptions propagate.
from harness import *

log = []
def spin():
    for _ in range(2): pass
class Ticks:
    def __init__(self, n): self.n = n
    def __aiter__(self): return self
    async def __anext__(self):
        if not self.n: raise StopAsyncIteration
        self.n -= 1; return self.n
class Meta(type):
    def __await__(cls):
        spin(); log.append(("await", cls.__name__)); return iter(())
    def __aiter__(cls):
        spin(); log.append(("aiter", cls.__name__)); return Ticks(2)
class Reading:
    def __init__(self, fail): self.fail = fail
    def __get__(self, cls, meta):
        spin(); log.append(("get", cls.__name__))
        if self.fail: raise self.fail("read")
        return lambda: (log.append("got"), iter(()))[1]
class Described(type):
    __await__ = Reading(None)
class Absent(type):
    __await__ = Reading(AttributeError)
    __aiter__ = Reading(AttributeError)
class Raising(type):
    __aiter__ = Reading(KeyError)
class K(metaclass=Meta): pass
class D(metaclass=Described): pass
class A(metaclass=Absent): pass
class R(metaclass=Raising): pass

async def awaits(cls): await cls; return "done"
async def loops(cls):
    out = []
    async for x in cls: out.append(x)
    return out
async def comprehends(cls): return [x async for x in cls]
def run(coro):
    del log[:]
    try: coro.send(None)
    except StopIteration as stop: return stop.value, log[:]
    except Exception as e: return (type(e).__name__, str(e)), log[:]
def cases():
    return [run(awaits(K)), run(loops(K)), run(comprehends(K)), run(awaits(D)),
            run(awaits(A)), run(loops(A)), run(comprehends(R))]
expected = [("done", [("await", "K")]), ([1, 0], [("aiter", "K")]), ([1, 0], [("aiter", "K")]), ("done", [("get", "D"), "got"]),
            (("AttributeError", "object Absent does not have __await__ method"), [("get", "A")]),
            (("AttributeError", "object Absent does not have __aiter__ method"), [("get", "A")]),
            (("KeyError", "'read'"), [("get", "R")])]
assert_eq(cases(), expected)
assert_eq(cases(), expected)
