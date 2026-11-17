# spec: PLS-315 27.2.2, 27.4.2
# description: a generator's or coroutine's send, throw, close and
# __next__ read from its type and called with the generator first, as
# G.send(g, v), type(g).send(g, v) or with a computed argument, resume it
# as its bound methods do: the value sent arrives at the yield, a thrown
# exception raises there and may be handled, close runs its finally, and
# __next__ sends None; a coroutine's return value is its StopIteration's.
# A wrong argument count or a non-generator first argument raises
# TypeError, an exhausted generator StopIteration. Inside functions as at
# module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

def gen():
    spin()
    try:
        x = yield 1
        spin()
        log.append(("got", x))
        yield x
    except KeyError as e:
        spin()
        log.append(("caught", str(e)))
        yield "handled"
    finally:
        log.append("finally")

async def co():
    spin()
    return 5

def error(call):
    try:
        return call()
    except Exception as e:
        return type(e).__name__, str(e)

def calls():
    del log[:]
    G = type(gen())
    out = []
    g = gen()
    out += [G.__next__(g), G.send(g, 4), error(lambda: G.__next__(g))]
    g = gen()
    out += [type(g).__next__(g), type(g).send(g, str(7))]
    g = gen()
    next(g)
    out += [G.throw(g, KeyError("k")), type(g).close(g), G.close(g)]
    g = gen()
    next(g)
    out.append(type(g).throw(g, KeyError(str("t"))))
    c = co()
    out.append(error(lambda: type(c).send(c, None)))
    out += [error(lambda: G.send(gen())), error(lambda: G.send(gen(), 1, 2)), error(lambda: G.send(5, 1)),
            error(lambda: G.close(gen(), 1)), error(lambda: G.send(gen(), 1))]
    return out, list(log)

expected = ([1, 4, ("StopIteration", ""), 1, "7", "handled", None, None, "handled", ("StopIteration", "5"),
             ("TypeError", "generator.send() takes exactly one argument (0 given)"),
             ("TypeError", "generator.send() takes exactly one argument (2 given)"),
             ("TypeError", "descriptor 'send' for 'generator' objects doesn't apply to a 'int' object"),
             ("TypeError", "generator.close() takes no arguments (1 given)"),
             ("TypeError", "can't send non-None value to a just-started generator")],
            [("got", 4), "finally", ("got", "7"), "finally", ("caught", "'k'"), "finally", ("caught", "'t'")])

def main():
    return calls()

assert_eq(main(), expected)
assert_eq(calls(), expected)
