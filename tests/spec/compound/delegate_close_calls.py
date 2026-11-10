# spec: PLS-315 13.16.3, 27.2.1, 27.2.2
# description: close() of a generator suspended in a yield from closes the
# delegate first, then raises a new GeneratorExit at the yield from, also
# when the delegate caught its own and returned; a delegate that yields
# instead raises RuntimeError there, and its other exceptions raise there
# as they are. Each frame of a chain may handle what reaches it, and the
# outermost's return value is close()'s, inside functions as at module
# level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

def context(e):
    return type(e.__context__).__name__

def inner(mode):
    try:
        yield "i"
    except GeneratorExit as e:
        spin()
        log.append(("inner", mode, e.args, context(e)))
        if mode == "return": return "ignored"
        if mode == "yield": yield "again"
        if mode == "raise": raise KeyError(mode)
        raise

def middle(mode):
    try:
        yield from inner(mode)
    except GeneratorExit as e:
        spin()
        log.append(("middle exit", e.args, context(e)))
        if mode == "return": return "m"
        raise
    except RuntimeError as e:
        spin()
        log.append(("middle", str(e), context(e)))
        if mode == "yield": return "m"
    except KeyError as e:
        spin()
        log.append(("middle caught", str(e)))
        yield "stubborn"

def outer(mode):
    if mode == "own":
        try:
            raise IndexError
        except IndexError:
            try:
                yield from middle(mode)
            except GeneratorExit as e:
                spin()
                log.append(("outer", context(e)))
                raise
    try:
        got = yield from middle(mode)
        log.append(("outer got", got))
    except GeneratorExit:
        spin()
        log.append("outer exit")
        if mode == "return": return "o"
        raise
    except RuntimeError as e:
        spin()
        log.append(("outer", str(e)))
        return "from outer"

def rethrown():
    try:
        yield from inner("yield")
    except RuntimeError as e:
        spin()
        log.append(("rethrown", context(e)))
        raise

def owner():
    try:
        raise IndexError
    except IndexError:
        try:
            yield from rethrown()
        except RuntimeError as e:
            spin()
            log.append(("owner", context(e)))

def close(mode):
    g = owner() if mode == "owner" else outer(mode)
    next(g)
    try:
        return ("closed", g.close(), g.gi_frame is None)
    except BaseException as e:
        return (type(e).__name__, str(e))

def results():
    del log[:]
    out = [close(mode) for mode in ["exit", "return", "yield", "raise"]]
    out.append(list(log))
    del log[:]
    try:
        raise ValueError
    except ValueError:
        out.append([close(mode) for mode in ["exit", "yield", "own", "owner"]])
    out.append(list(log))
    return out

expected = [("closed", None, True), ("closed", "o", True), ("closed", None, True),
            ("closed", "from outer", True),
            [("inner", "exit", (), "NoneType"), ("middle exit", (), "NoneType"), "outer exit",
             ("inner", "return", (), "NoneType"), ("middle exit", (), "NoneType"), "outer exit",
             ("inner", "yield", (), "NoneType"), ("middle", "generator ignored GeneratorExit", "NoneType"), "outer exit",
             ("inner", "raise", (), "NoneType"), ("middle caught", "'raise'"), ("outer", "generator ignored GeneratorExit")],
            [("closed", None, True)] * 4,
            [("inner", "exit", (), "ValueError"), ("middle exit", (), "ValueError"), "outer exit",
             ("inner", "yield", (), "ValueError"), ("middle", "generator ignored GeneratorExit", "ValueError"), "outer exit",
             ("inner", "own", (), "ValueError"), ("middle exit", (), "ValueError"), ("outer", "IndexError"),
             ("inner", "yield", (), "ValueError"), ("rethrown", "ValueError"), ("owner", "IndexError")]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
g = outer("return")
next(g)
assert_eq(g.close(), "o")
