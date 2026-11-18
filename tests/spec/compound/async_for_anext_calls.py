# spec: PLS-315 15.3.2, 13.2.6
# description: async for, and an async comprehension, over an instance
# whose __anext__ is a plain Python function, or a lambda, calls it for
# each item, which may loop, and awaits what it returns: a coroutine, or
# an object whose __await__ is a generator, its yields passing to the
# driver. StopAsyncIteration raised by __anext__ ends the loop, running
# its else; another exception propagates; a result that cannot be awaited
# raises TypeError with its error as the cause. A break skips the else.
from harness import *

log = []
def spin():
    for _ in range(2): pass
class Fut:
    def __init__(self, v): self.v = v
    def __await__(self):
        r = yield ("fut", self.v)
        return (self.v, r)
async def value(v):
    return v
class AI:
    def __init__(self, n, how="co"): self.i = 0; self.n = n; self.how = how
    def __aiter__(self): return self
    def __anext__(self):
        spin(); log.append(("anext", self.i))
        if self.i >= self.n:
            if self.how == "key": raise KeyError("end")
            raise StopAsyncIteration
        self.i += 1
        if self.how == "fut": return Fut(self.i)
        if self.how == "bad": return self.i
        return value(self.i)
class L:
    def __aiter__(self): return self
    __anext__ = lambda self: value(1) if not log.append("lam") and len(log) < 3 else (_ for _ in ()).throw(StopAsyncIteration)
def err(e): return (type(e).__name__, str(e), type(e.__cause__).__name__)
async def main():
    out = []
    async for x in AI(2): out.append(x)
    else: out.append("else")
    async for x in AI(3, "fut"):
        out.append(x)
        if x == 2: break
    else: out.append("no")
    try:
        async for x in AI(1, "key"): out.append(x)
    except KeyError as e: out.append(err(e))
    try:
        async for x in AI(2, "bad"): out.append(x)
    except TypeError as e: out.append(err(e))
    out.append([x async for x in AI(3)])
    out.append([(x, y) async for x in AI(2) async for y in AI(x)])
    del log[:]
    out.append([x async for x in L()])
    async for x in AI(1):
        async for y in AI(2, "fut"): out.append((x, y))
    return out
def run(c):
    v = None
    while True:
        try: c.send(v)
        except StopIteration as e: return e.value
        v = "s"
def go():
    del log[:]
    r = run(main())
    return r, list(log)

expected = ([1, 2, 'else', (1, 's'), (2, 's'), (3, 's'), 'no', 1, ('KeyError', "'end'", 'NoneType'), ('TypeError', "'async for' received an invalid object from __anext__: int", 'TypeError'), [1, 2, 3], [(1, 1), (2, 1), (2, 2)], [1, 1], (1, (1, 's')), (1, (2, 's'))],
            ['lam', 'lam', 'lam', ('anext', 0), ('anext', 0), ('anext', 1), ('anext', 2), ('anext', 1)])

assert_eq(go(), expected)
assert_eq(go(), expected)
