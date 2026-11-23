# spec: PLS-315 7.3.2, 7.7.1, 7.7.4, 7.7.5, 13.4, 13.16.3, 15.3.1, 15.3.2
# description: a for loop, a comprehension, a yield from, an async for
# and an await read their __iter__, __aiter__, __anext__ or __await__ from
# a descriptor's Python __get__ before calling what it gives; an
# AttributeError of the read makes __iter__ absent, a TypeError "'T'
# object is not iterable", and the async methods' AttributeError "object
# T does not have M method"; any other exception propagates. Inside
# functions as at module level.
from harness import *

log = []
class Get:
    def __init__(self, give): self.give = give
    def __get__(self, obj, cls):
        for _ in range(2): pass
        log.append("get")
        if isinstance(self.give, BaseException): raise self.give
        return self.give.__get__(obj, cls)

def make(name, give, base=object):
    return type("T", (base,), {name: Get(give)})()

def run(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))

def gen(o):
    r = yield from o
    return r

async def over(o):
    return [x async for x in o]

async def looped(o):
    out = []
    async for x in o: out.append(x)
    return out

async def awaited(o):
    return await o

def drive(co):
    try: co.send(None)
    except StopIteration as e: return ("done", e.value)
    except Exception as e: return (type(e).__name__, str(e))

class AIt:
    def __init__(self): self.n = 0
    def __aiter__(self): return self
    async def __anext__(self):
        self.n += 1
        if self.n > 2: raise StopAsyncIteration
        return self.n

def iterate(self): log.append("iter"); return iter([1, 2])
def aiter_self(self): log.append("aiter"); return AIt()
def await_it(self): log.append("await"); return iter(())
class AN:
    def __aiter__(self): return self
async def an_next(self): raise StopAsyncIteration

def results():
    out = []
    for give in (iterate, AttributeError("a"), KeyError("k")):
        out.append([run(lambda: [x for x in make("__iter__", give)]), run(lambda: list(gen(make("__iter__", give)))),
                    run(lambda: [x for x in make("__iter__", give) for y in (1,)])])
        out.append(log[:]); log.clear()
    for give in (aiter_self, AttributeError("a"), KeyError("k")):
        out.append([drive(over(make("__aiter__", give))), drive(looped(make("__aiter__", give)))])
        out.append(log[:]); log.clear()
    for give in (await_it, AttributeError("a"), KeyError("k")):
        out.append(drive(awaited(make("__await__", give))))
        out.append(log[:]); log.clear()
    for give in (an_next, AttributeError("a"), KeyError("k")):
        out.append(drive(looped(type("N", (AN,), {"__anext__": Get(give)})())))
        out.append(log[:]); log.clear()
    for x in make("__iter__", iterate): log.append(x)
    out.append(log[:]); log.clear()
    return out

absent = ("TypeError", "'T' object is not iterable")
expected = [[[1, 2], [1, 2], [1, 2]], ["get", "iter"] * 3,
            [absent] * 3, ["get"] * 3,
            [("KeyError", "'k'")] * 3, ["get"] * 3,
            [("done", [1, 2])] * 2, ["get", "aiter"] * 2,
            [("AttributeError", "object T does not have __aiter__ method")] * 2, ["get"] * 2,
            [("KeyError", "'k'")] * 2, ["get"] * 2,
            ("done", None), ["get", "await"],
            ("AttributeError", "object T does not have __await__ method"), ["get"],
            ("KeyError", "'k'"), ["get"],
            ("done", []), ["get"],
            ("AttributeError", "object N does not have __anext__ method"), ["get"],
            ("KeyError", "'k'"), ["get"],
            ["get", "iter", 1, 2]]

assert_eq(results(), expected)
def main():
    return results()
assert_eq(main(), expected)

# A class whose metaclass's descriptor raises AttributeError lacks the
# method the same way, named by the metaclass.
class AbsentMeta(type):
    @property
    def __await__(cls): raise AttributeError("x")
    @property
    def __aiter__(cls): raise AttributeError("x")
class AbsentKind(metaclass=AbsentMeta): pass
async def meta_awaits(): await AbsentKind
async def meta_loops():
    async for x in AbsentKind: pass
async def meta_comp(): return [x async for x in AbsentKind]
meta_messages = []
for meta_f in (meta_awaits, meta_loops, meta_comp):
    try: meta_f().send(None)
    except AttributeError as e: meta_messages.append(str(e))
assert_eq(meta_messages, ["object AbsentMeta does not have __await__ method"] + ["object AbsentMeta does not have __aiter__ method"] * 2)
