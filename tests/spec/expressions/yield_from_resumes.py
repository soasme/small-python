# spec: PLS-315 13.16.3, 27.2.1
# description: A yield from of a generator gives its resumer each value the
# delegate yields and sends it what the resumer sends; the delegate's return
# is the yield from's value, and what it raises, a StopIteration made a
# RuntimeError, raises there. Chains of yield from, delegates already
# started, a running delegate, close and throw behave alike whether a loop,
# next(), send() or list() resumes the outer generator, in function
# statements as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

def inner(tag):
    spin()
    got = yield tag + "1"
    log.append((tag, got))
    spin()
    got = yield tag + "2"
    log.append((tag, got))
    return tag + "!"

def outer(tag):
    spin()
    result = yield from inner(tag)
    log.append(("outer", result))
    yield result

def chain(depth):
    if depth:
        result = yield from chain(depth - 1)
        return result + 1
    yield "bottom"
    return 0

def failing():
    spin()
    yield 1
    raise KeyError("inner")

def catching():
    try:
        yield from failing()
    except KeyError as e:
        yield ("caught", str(e))

def stopping():
    yield 1
    raise StopIteration(5)

def stopped():
    try:
        yield from stopping()
    except RuntimeError as e:
        yield (type(e.__cause__).__name__, str(e))

def started():
    it = inner("s")
    next(it)
    result = yield from it
    yield result

def watched():
    it = inner("w")
    yield from it

def closing():
    try:
        spin()
        yield 1
        yield 2
    finally:
        log.append("inner closed")

def delegating_close():
    try:
        yield from closing()
    finally:
        log.append("outer closed")

def thrown_into():
    try:
        yield 1
    except ValueError as e:
        yield ("inner caught", str(e))

def self_delegate():
    yield from me

def run():
    del log[:]
    out = [list(outer("a"))]
    g = outer("b")
    out.append([next(g), g.send("x"), g.send("y")])
    out.append([v for v in chain(30)])
    c = chain(30)
    out.append(next(c))
    try:
        next(c)
    except StopIteration as e:
        out.append(e.value)
    out.append(list(catching()))
    out.append(list(stopped()))
    out.append(list(started()))
    w = watched()
    next(w)
    out.append((w.gi_yieldfrom.__name__, w.gi_running, w.gi_yieldfrom.gi_running))
    d = delegating_close()
    next(d)
    d.close()
    out.append(d.gi_yieldfrom)
    th = (lambda: (yield from thrown_into()))()
    next(th)
    out.append(th.throw(ValueError("v")))
    global me
    me = self_delegate()
    try:
        next(me)
    except ValueError as e:
        out.append(str(e))
    out.append(list(log))
    return out

expected = [["a1", "a2", "a!"],
            ["b1", "b2", "b!"],
            ["bottom"],
            "bottom", 30,
            [1, ("caught", "'inner'")],
            [1, ("StopIteration", "generator raised StopIteration")],
            ["s2", "s!"],
            ("inner", False, False),
            None,
            ("inner caught", "v"),
            "generator already executing",
            [("a", None), ("a", None), ("outer", "a!"),
             ("b", "x"), ("b", "y"), ("outer", "b!"),
             ("s", None), ("s", None),
             "inner closed", "outer closed"]]

def main():
    return run()

assert_eq(main(), expected)
assert_eq(main(), expected)
assert_eq(run(), expected)
