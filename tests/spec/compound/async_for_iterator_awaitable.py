# spec: PLS-315 15.3.2
# description: An async for whose iterator's __anext__ is a plain method
# returning an awaitable, whose __await__ gives a builtin iterator, awaits
# it: each value the iterator yields suspends the coroutine, also when it
# is awaited by another coroutine, and the iterator's end gives the item;
# a coroutine sent to while suspended there goes on from that await.
from harness import *

class Ticket:
    def __await__(self): return iter(["tick"])

class Tickets:
    def __init__(self): self.n = 0
    def __aiter__(self): return self
    def __anext__(self):
        self.n += 1
        if self.n > 2: raise StopAsyncIteration
        return Ticket()

async def body():
    out = []
    async for item in Tickets(): out.append(item)
    return out

async def outer():
    return await body()

def drive(coroutine):
    sent = []
    try:
        while True: sent.append(coroutine.send(None))
    except StopIteration as e:
        return sent, e.value

def results():
    return [drive(body()), drive(outer())]

expected = [(["tick", "tick"], [None, None]), (["tick", "tick"], [None, None])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
