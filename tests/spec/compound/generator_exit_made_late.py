# spec: PLS-315 13.16.3, 27.2.2
# description: throw() of a GeneratorExit subclass whose __init__ or
# __new__ is Python, which may loop, into a generator or coroutine
# suspended in a yield from or await closes the delegates first, then
# makes the exception at the outermost, which may catch it; an error
# making it raises there instead; an exception the generator handles is
# its context. Inside functions as at module level.
from harness import *

log = []

class Exit(GeneratorExit):
    def __init__(self, *args):
        for _ in range(2): pass
        log.append("made")
        super().__init__(*args)

class New(GeneratorExit):
    def __new__(cls, *args):
        for _ in range(2): pass
        log.append("new")
        return super().__new__(cls, *args)

class Broken(GeneratorExit):
    def __init__(self):
        for _ in range(2): pass
        log.append("broken")
        raise LookupError("init")

def inner(name):
    try:
        yield name
    finally:
        log.append(name + " closed")

def middle():
    yield from inner("inner")

def outer(source):
    try:
        yield from source
    except BaseException as e:
        for _ in range(2): pass
        log.append(("caught", type(e).__name__, type(e.__context__).__name__))
        yield "handled"

def handling(source):
    try:
        raise KeyError("held")
    except KeyError:
        try:
            yield from source
        except BaseException as e:
            log.append(("caught", type(e).__name__, type(e.__context__).__name__))
            yield "handled"

class Await:
    def __await__(self):
        try:
            yield "await"
        finally:
            log.append("await closed")

async def inner_co():
    await Await()

async def outer_co():
    try:
        await inner_co()
    except BaseException as e:
        log.append(("caught", type(e).__name__, type(e.__context__).__name__))
        return "handled"

def run(g, k):
    del log[:]
    out = [g.send(None)]
    try:
        out.append(g.throw(k))
    except StopIteration as e:
        out.append(("stop", e.value))
    except BaseException as e:
        out.append((type(e).__name__, str(e)))
    return out, log[:]

def cases():
    return [run(outer(inner("inner")), Exit), run(outer(middle()), Exit), run(outer(inner("inner")), New),
            run(outer(middle()), Broken), run(handling(inner("inner")), Exit), run(outer_co(), Exit),
            run(outer(inner("inner")), GeneratorExit)]

expected = [
    (["inner", "handled"], ["inner closed", "made", ("caught", "Exit", "NoneType")]),
    (["inner", "handled"], ["inner closed", "made", ("caught", "Exit", "NoneType")]),
    (["inner", "handled"], ["inner closed", "new", ("caught", "New", "NoneType")]),
    (["inner", "handled"], ["inner closed", "broken", ("caught", "LookupError", "NoneType")]),
    (["inner", "handled"], ["inner closed", "made", ("caught", "Exit", "KeyError")]),
    (["await", ("stop", "handled")], ["await closed", "made", ("caught", "Exit", "NoneType")]),
    (["inner", "handled"], ["inner closed", ("caught", "GeneratorExit", "NoneType")]),
]

def main():
    return cases()

assert_eq(main(), expected)
assert_eq(cases(), expected)
