# spec: PLS-315 13.16.3
# description: A yield from of an iterator whose class has a Python
# __next__ calls it for each item the resumer asks for, sending None, and
# its send for any other value; a StopIteration it raises ends the yield
# from with its value, a subclass too, and any other exception raises
# there. While __next__ runs, the delegating generator is running, and
# its gi_yieldfrom is not the iterator. throw and close go to the iterator's
# methods; chains of yield from, a loop, list() and an await of the
# iterator behave alike, as do a send the iterator itself holds and a
# callable iterator's resumptions, inside functions as at module level.
from harness import *

log = []

class It:
    def __init__(self, n, fail=None): self.i = 0; self.n = n; self.fail = fail
    def __iter__(self): return self
    def __next__(self):
        for _ in range(2): pass
        self.i += 1
        log.append(("next", self.i))
        if self.i == self.fail: raise KeyError(self.i)
        if self.i > self.n: raise StopIteration(self.i * 10)
        return self.i
    def send(self, v):
        log.append(("send", v))
        return self.__next__()
    def throw(self, *a):
        log.append(("throw", a[0].__name__))
        return 99
    def close(self): log.append("close")

def g(it):
    r = yield from it
    log.append(("ret", r))
    yield r

class Running:
    def __iter__(self): return self
    def __next__(self):
        try: next(gen)
        except ValueError as e: log.append(str(e))
        log.append((gen.gi_yieldfrom is self, gen.gi_running))
        raise StopIteration

class Sub(StopIteration): pass

class Raising:
    def __iter__(self): return self
    def __next__(self): raise Sub(5)

def outer(it):
    v = yield from g(it)
    yield ("outer", v)

def deep(n):
    if n == 0:
        return (yield from It(1))
    return (yield from deep(n - 1))

class Awaited:
    def __await__(self): return It(2)

async def co():
    return await Awaited()

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    global gen
    del log[:]
    out = [list(g(It(3)))]
    x = g(It(5))
    out.append([next(x), x.send(None), x.send(7), x.throw(ValueError), next(x)])
    x.close()
    out.append(error(lambda: list(g(It(5, fail=2)))))
    gen = g(Running())
    out.append(list(gen))
    out.append(list(g(Raising())))
    items = []
    for v in outer(It(2)): items.append(v)
    out.append(items)
    out.append(list(deep(30)))
    c = co()
    try:
        while True: out.append(c.send(None))
    except StopIteration as e: out.append(e.value)
    out.append(list(log))
    return out

expected = [[1, 2, 3, 40], [1, 2, 3, 99, 4], ("KeyError", "2"), [None], [5], [1, 2, 30, ("outer", None)], [1],
            1, 2, 30,
            [("next", 1), ("next", 2), ("next", 3), ("next", 4), ("ret", 40),
             ("next", 1), ("next", 2), ("send", 7), ("next", 3), ("throw", "ValueError"), ("next", 4), "close",
             ("next", 1), ("next", 2),
             "generator already executing", (False, True), ("ret", None), ("ret", 5),
             ("next", 1), ("next", 2), ("next", 3), ("ret", 30),
             ("next", 1), ("next", 2), ("next", 1), ("next", 2), ("next", 3)]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)

# A send found on the iterator itself, and a resumption by a callable
# iterator's calls, behave alike.
def own():
    del log[:]
    it = It(3); it.send = lambda v: ("own", v)
    x = g(it)
    out = [next(x), x.send(5), next(x)]
    out.append(list(iter(g(It(3)).__next__, 40)))
    bare = g(Bare())
    out += [next(bare), error(lambda: bare.send(1))]
    return out

class Bare:
    def __iter__(self): return self
    def __next__(self):
        for _ in range(2): pass
        return "bare"

assert_eq(own(), [1, ("own", 5), 2, [1, 2, 3], "bare", ("AttributeError", "'Bare' object has no attribute 'send'")])
