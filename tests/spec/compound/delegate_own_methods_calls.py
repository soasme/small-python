# spec: PLS-315 13.16.3
# description: A yield from of an iterator holding its own send, throw or
# close as instance attributes calls them, not its class's, with the
# sent value or the thrown exception alone, no self: send's result is the
# next item, throw's too, and close is called once on a close of the
# delegating generator. A StopIteration from send ends the yield from
# with its value.
from harness import *

log = []
class It:
    def __iter__(self): return self
    def __next__(self):
        for _ in (): pass
        log.append("next")
        return 1
    def send(self, v): log.append("class send"); return 0
    def throw(self, *a): log.append("class throw"); return 0
    def close(self): log.append("class close")

def g(it):
    r = yield from it
    log.append(("ret", r))
    yield r

def own_send(v):
    for _ in (): pass
    log.append(("send", v))
    if v == "stop": raise StopIteration("done")
    return ("sent", v)
def own_throw(e):
    for _ in (): pass
    log.append(("throw", type(e).__name__))
    return "thrown"
def own_close():
    for _ in (): pass
    log.append("close")

def results():
    for _ in (): pass
    del log[:]
    it = It(); it.send = own_send; it.throw = own_throw; it.close = own_close
    x = g(it)
    out = [next(x), x.send(5), x.throw(KeyError("k")), x.send("stop")]
    y = g(it)
    out.append(next(y))
    y.close()
    return out, list(log)

expected = ([1, ("sent", 5), "thrown", "done", 1],
            ["next", ("send", 5), ("throw", "KeyError"), ("send", "stop"), ("ret", "done"), "next", "close"])

assert_eq(results(), expected)
assert_eq(results(), expected)
