# spec: PLS-315 13.4.1 15.3.2 27.4.2
# description: A coroutine suspended in an await, or an async for's await,
# of an iterator that is no generator, a builtin's or an instance's whose
# __next__ is Python, resumes it on each send: the iterator's values are
# passed out, its end is the await's value, a value sent that is not None
# needs a send method, and a throw raises at the await, as the iterator
# has no throw.
from harness import *

class Ticks:
    def __init__(self, *values): self.values = values
    def __await__(self): return iter(self.values)

class Counter:
    def __init__(self, n): self.i = 0; self.n = n
    def __iter__(self): return self
    def __next__(self):
        self.i += 1
        if self.i > self.n: raise StopIteration(self.i * 100)
        return ("count", self.i)

class Counted:
    def __await__(self): return Counter(2)

class Source:
    def __init__(self, n): self.i = 0; self.n = n
    def __aiter__(self): return self
    def __anext__(self):
        self.i += 1
        if self.i > self.n: raise StopAsyncIteration
        return Counted() if self.i % 2 else Ticks("a", "b")

async def awaits():
    x = await Ticks(1, 2, 3)
    y = await Counted()
    return [x, y]

async def loops():
    out = []
    async for item in Source(3): out.append(item)
    return out

async def caught():
    try:
        await Ticks(1, 2)
    except KeyError as e:
        return ["caught", e.args]

def drive(coroutine, sent=None):
    out = []
    try:
        out.append(coroutine.send(None))
        while True: out.append(coroutine.send(sent))
    except StopIteration as e:
        return out, e.value
    except AttributeError as e:
        return out, "AttributeError"

def thrown():
    coroutine = caught()
    first = coroutine.send(None)
    try:
        coroutine.throw(KeyError("k"))
    except StopIteration as e:
        return first, e.value

def results():
    return [drive(awaits()), drive(loops()), drive(awaits(), 5), thrown()]

expected = [
    ([1, 2, 3, ("count", 1), ("count", 2)], [None, 300]),
    ([("count", 1), ("count", 2), "a", "b", ("count", 1), ("count", 2)], [300, None, 300]),
    ([1], "AttributeError"),
    (1, ["caught", ("k",)]),
]

assert_eq(results(), expected)
assert_eq(results(), expected)
