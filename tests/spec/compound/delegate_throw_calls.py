# spec: PLS-315 13.16.3, 27.2.1, 27.2.2, 13.4
# description: throw() into a generator suspended in a yield from, or a
# coroutine suspended in an await, raises the exception at the innermost
# suspended yield: a handler there may yield again, which is throw()'s
# value, or return, ending the delegation with that value; an exception no
# frame handles leaves the outermost, and each frame it passes may handle
# it, chained again to the exception that frame handles. A throw of
# GeneratorExit closes the delegate first, raising a new one, chained as
# close()'s are, then the thrown one in the outermost, inside functions as
# at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

def inner(tag):
    try:
        yield tag + "1"
    except KeyError as e:
        spin()
        log.append(("inner caught", tag, str(e)))
        yield tag + "2"
    except IndexError:
        spin()
        log.append(("inner returns", tag))
        return "early"
    except GeneratorExit as e:
        log.append(("inner exit", tag, e.args, type(e.__context__).__name__))
        raise
    yield tag + "3"
    return "done"

def middle(tag):
    try:
        got = yield from inner(tag)
    except ValueError as e:
        spin()
        log.append(("middle caught", tag, str(e)))
        got = "handled"
    yield ("middle", got)

def owner():
    try:
        raise IndexError
    except IndexError:
        try:
            yield from middle("o")
        except TypeError as e:
            spin()
            log.append(("owner", type(e.__context__).__name__))
            yield "owned"

def outer(tag):
    result = yield from middle(tag)
    return result

class Y:
    def __await__(self):
        try:
            got = yield "y"
        except KeyError:
            spin()
            return "awaited handled"
        return got

async def leaf():
    return await Y()

async def top():
    spin()
    return ("top", await leaf())

def exit_thrown():
    g = outer("x")
    next(g)
    exit = GeneratorExit("mine")
    try:
        raise ValueError
    except ValueError:
        try:
            g.throw(exit)
        except GeneratorExit as e:
            return e is exit, e.__context__

def steps(g, actions):
    out = []
    for action in actions:
        try:
            if action is None: out.append(g.send(None))
            elif isinstance(action, str): out.append(g.send(action))
            else: out.append(g.throw(action))
        except StopIteration as e:
            out.append(("returned", e.value)); break
        except BaseException as e:
            out.append((type(e).__name__, str(e))); break
    return out

def results():
    del log[:]
    return [steps(outer("a"), [None, KeyError("k"), None, None]),
            steps(outer("b"), [None, IndexError, None]),
            steps(outer("c"), [None, ValueError("v"), None]),
            steps(outer("d"), [None, TypeError("t")]),
            steps(outer("e"), [None, GeneratorExit]),
            steps(owner(), [None, TypeError]),
            exit_thrown(),
            steps(top(), [None, KeyError("k")]),
            steps(top(), [None, ValueError("w")]),
            list(log)]

expected = [["a1", "a2", "a3", ("middle", "done")],
            ["b1", ("middle", "early"), ("returned", None)],
            ["c1", ("middle", "handled"), ("returned", None)],
            ["d1", ("TypeError", "t")],
            ["e1", ("GeneratorExit", "")],
            ["o1", "owned"],
            (True, None),
            ["y", ("returned", ("top", "awaited handled"))],
            ["y", ("ValueError", "w")],
            [("inner caught", "a", "'k'"), ("inner returns", "b"), ("middle caught", "c", "v"), ("inner exit", "e", (), "NoneType"), ("owner", "IndexError"),
             ("inner exit", "x", (), "ValueError")]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
g = outer("m")
assert_eq([next(g), g.throw(KeyError("x")), next(g)], ["m1", "m2", "m3"])
g = outer("n")
next(g)
assert_eq(g.throw(ValueError("z")), ("middle", "handled"))
