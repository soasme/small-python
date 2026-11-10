# spec: PLS-315 13.16.3, 27.2.1, 27.2.2, 13.4
# description: throw() into a generator suspended in a yield from of an
# iterator instance, or a coroutine suspended in an await of one, calls the
# instance's throw with throw()'s argument: its value is throw()'s, a StopIteration ends the
# delegation with its value, and another exception raises at the yield
# from, chained to the exception the frame handles. close(), or a throw of
# GeneratorExit, calls the instance's close, then raises the GeneratorExit
# at the yield from, a thrown one itself; an error from close raises there
# instead, and a generator dropped while delegating closes its delegate. An instance whose throw or close is gone
# when the throw raises passes the exception to the yield from, inside
# functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class It:
    def __init__(self, n): self.n = n
    def __iter__(self): return self
    def __next__(self):
        spin()
        if self.n == 0: raise StopIteration("end")
        self.n -= 1
        return self.n
    def throw(self, e):
        spin()
        log.append(("throw", type(e).__name__))
        if isinstance(e, KeyError): return "caught"
        if isinstance(e, IndexError): raise StopIteration("stopped")
        raise ValueError("from throw")
    def close(self):
        spin()
        log.append("close")

class BadClose(It):
    def close(self):
        spin()
        raise TypeError("bad close")

class Fleeting:
    def __iter__(self): return self
    def __next__(self):
        spin()
        return 1
    def throw(self, e):
        spin()
        return "kept"
    def close(self):
        spin()

class Vanishing(Exception):
    def __init__(self):
        del Fleeting.throw
        super().__init__()

class Leaving(GeneratorExit):
    def __init__(self):
        del Fleeting.close
        super().__init__()

def outer(it):
    try:
        r = yield from it
        log.append(("returned", r))
        yield "after"
    except ValueError as e:
        log.append(("outer caught", str(e), type(e.__context__).__name__))
        yield "handled"

def mid(it):
    r = yield from outer(it)
    return r

class Awaited:
    def __await__(self):
        return It(3)

async def awaiting():
    try:
        return await Awaited()
    except ValueError:
        spin()
        return "await handled"

def steps(g, actions):
    out = []
    for a in actions:
        try:
            out.append(g.send(None) if a is None else g.close() if a == "close" else g.throw(a))
        except StopIteration as e:
            out.append(("stop", e.value)); break
        except BaseException as e:
            out.append((type(e).__name__, str(e), type(e.__context__).__name__)); break
    return out

def handling():
    g = outer(It(3)); next(g)
    try:
        raise OSError
    except OSError:
        return steps(g, [TypeError("t")])

def exit_thrown(make):
    g = make(It(3)); next(g)
    exit = GeneratorExit("mine")
    try:
        g.throw(exit)
    except GeneratorExit as e:
        return e is exit, e.args

def results():
    del log[:]
    return [steps(outer(It(3)), [None, KeyError("k"), None]),
            steps(outer(It(3)), [None, IndexError("i"), None]),
            steps(outer(It(3)), [None, KeyError, None]),
            steps(outer(It(3)), [None, TypeError("t"), None]),
            steps(mid(It(3)), [None, KeyError("k"), TypeError("t")]),
            steps(outer(It(3)), [None, "close"]),
            steps(mid(It(3)), [None, "close"]),
            steps(outer(BadClose(3)), [None, "close"]),
            steps(mid(BadClose(3)), [None, GeneratorExit]),
            exit_thrown(outer), exit_thrown(mid),
            handling(),
            steps(awaiting(), [None, KeyError("k")]),
            steps(awaiting(), [None, TypeError("t")]),
            list(log)]

expected = [[2, "caught", 1],
            [2, "after", ("stop", None)],
            [2, "handled", ("stop", None)],
            [2, "handled", ("stop", None)],
            [2, "caught", "handled"],
            [2, None],
            [2, None],
            [2, ("TypeError", "bad close", "NoneType")],
            [2, ("TypeError", "bad close", "NoneType")],
            (True, ("mine",)), (True, ("mine",)),
            ["handled"],
            [2, "caught"],
            [2, ("stop", "await handled")],
            [("throw", "KeyError"), "close", ("throw", "IndexError"), ("returned", "stopped"),
             ("throw", "type"), ("outer caught", "from throw", "NoneType"),
             ("throw", "TypeError"), ("outer caught", "from throw", "NoneType"),
             ("throw", "KeyError"), ("throw", "TypeError"), ("outer caught", "from throw", "NoneType"),
             "close", "close", "close", "close",
             ("throw", "TypeError"), ("outer caught", "from throw", "OSError"),
             ("throw", "KeyError"), "close", ("throw", "TypeError")]]

def vanished():
    g = outer(Fleeting()); next(g)
    first = g.throw(KeyError("k"))
    try:
        g.throw(Vanishing)
    except Vanishing:
        pass
    g = outer(Fleeting()); next(g)
    try:
        g.throw(Leaving)
    except Leaving as e:
        return first, type(e.__context__).__name__

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
assert_eq(vanished(), ("kept", "NoneType"))
g = outer(It(3))
assert_eq([next(g), g.throw(KeyError("x")), g.close(), log[-2:]], [2, "caught", None, [("throw", "KeyError"), "close"]])
