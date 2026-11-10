# spec: PLS-315 13.4, 27.3, 27.4.3
# description: await of a coroutine, or of an object whose __await__ is a
# generator, runs it inside the awaiting coroutine: what the innermost
# suspends with reaches the outermost send() and what that sends goes back
# down; the awaited coroutine's return value is the await's, its exception
# raises at the await, and a throw() or close() of the outermost reaches the
# innermost first. An awaited coroutine cannot be awaited again, and a
# StopIteration escaping one is a RuntimeError, inside functions as at
# module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Y:
    def __init__(self, tag): self.tag = tag
    def __await__(self):
        spin()
        got = yield self.tag
        log.append(("Y", self.tag, got))
        return got

async def leaf(tag):
    spin()
    try:
        got = await Y(tag)
    except KeyError as e:
        log.append(("leaf caught", tag))
        return "recovered"
    except GeneratorExit:
        log.append(("leaf exit", tag))
        raise
    if got == "fail": raise ValueError(tag)
    if got == "stop": raise StopIteration(tag)
    return got

async def middle(tag):
    spin()
    first = await leaf(tag + "1")
    second = await leaf(tag + "2")
    return (first, second)

async def top():
    spin()
    try:
        pair = await middle("m")
    except ValueError as e:
        return ("top caught", str(e))
    return ("top", pair)

def drive(coroutine, sends):
    out = []
    try:
        out.append(coroutine.send(None))
        for value in sends:
            if value is KeyError: out.append(coroutine.throw(KeyError("k")))
            else: out.append(coroutine.send(value))
    except StopIteration as e:
        out.append(("returned", e.value))
    except Exception as e:
        out.append((type(e).__name__, str(e)))
    return out

async def twice(coroutine):
    spin()
    await coroutine
    return await coroutine

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    out = [drive(top(), ["a", "b"]), drive(top(), ["fail"]), drive(top(), [KeyError, "z"]),
           drive(top(), ["stop"])]
    c = top()
    c.send(None)
    c.close()
    out.append(c.cr_frame is None)
    done = leaf("d")
    out.append(drive(twice(done), ["v", "w"]))
    out.append(list(log))
    return out

expected = [["m1", "m2", ("returned", ("top", ("a", "b")))],
            ["m1", ("returned", ("top caught", "m1"))],
            ["m1", "m2", ("returned", ("top", ("recovered", "z")))],
            ["m1", ("RuntimeError", "coroutine raised StopIteration")],
            True,
            ["d", ("RuntimeError", "cannot reuse already awaited coroutine")],
            [("Y", "m1", "a"), ("Y", "m2", "b"), ("Y", "m1", "fail"), ("leaf caught", "m1"), ("Y", "m2", "z"),
             ("Y", "m1", "stop"), ("leaf exit", "m1"), ("Y", "d", "v")]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
c = top()
assert_eq([c.send(None), c.send("p")], ["m1", "m2"])
try:
    c.send("q")
except StopIteration as e:
    assert_eq(e.value, ("top", ("p", "q")))
c = top()
c.send(None)
assert_eq(error(lambda: c.send("fail")), ("StopIteration", "('top caught', 'm1')"))
