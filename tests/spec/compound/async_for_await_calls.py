# spec: PLS-315 15.3.2, 7.7.5
# description: An async for whose __anext__ returns an instance awaits it
# through its class's __await__: a plain method, a generator function or
# one a descriptor gives, its iterator's values suspending the coroutine.
# Any failure to get that iterator, the method raising, returning what is
# no iterator or being absent, is a TypeError naming the instance, caused
# by the failure, which the coroutine may handle and go on.
from harness import *

class Plain:
    def __init__(self, v): self.v = v
    def __await__(self): return iter([self.v])

class Generated:
    def __init__(self, v): self.v = v
    def __await__(self):
        yield ("gen", self.v)
        return self.v * 10

class Described:
    def __init__(self, v): self.v = v
    @property
    def __await__(self):
        v = self.v
        return lambda: iter([("prop", v)])

class Raising:
    def __init__(self, v): pass
    def __await__(self): raise ValueError("no await")

class Wrong:
    def __init__(self, v): pass
    def __await__(self): return 5

class Absent:
    def __init__(self, v): pass
    @property
    def __await__(self): raise AttributeError("gone")

class Source:
    def __init__(self, kind, n): self.kind = kind; self.n = n; self.i = 0
    def __aiter__(self): return self
    def __anext__(self):
        self.i += 1
        if self.i > self.n: raise StopAsyncIteration
        return self.kind(self.i)

async def collect(kind, n):
    out = []
    async for item in Source(kind, n): out.append(item)
    return out

async def failing(kind):
    try:
        async for item in Source(kind, 2): pass
    except TypeError as e:
        return [str(e), type(e.__cause__).__name__, str(e.__cause__)]
    return "no error"

def drive(coroutine):
    sent = []
    try:
        while True: sent.append(coroutine.send(None))
    except StopIteration as e:
        return sent, e.value

def results():
    return [drive(collect(Plain, 2)), drive(collect(Generated, 2)), drive(collect(Described, 2)),
            drive(failing(Raising)), drive(failing(Wrong)), drive(failing(Absent))]

expected = [
    ([1, 2], [None, None]),
    ([("gen", 1), ("gen", 2)], [10, 20]),
    ([("prop", 1), ("prop", 2)], [None, None]),
    ([], ["'async for' received an invalid object from __anext__: Raising", "ValueError", "no await"]),
    ([], ["'async for' received an invalid object from __anext__: Wrong", "TypeError", 'Wrong.__await__() must return an iterator, not int']),
    ([], ["'async for' received an invalid object from __anext__: Absent", "AttributeError", "object Absent does not have __await__ method"]),
]

assert_eq(results(), expected)
assert_eq(results(), expected)
