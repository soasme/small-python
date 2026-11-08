# spec: PLS-315 27.2.1, 27.2.2, 13.16.1
# description: A generator's throw() resumes it at its yield, also a yield
# statement or one a yield from delegates to, raising the exception there:
# a class is instantiated, a handler that yields gives throw()'s value, one
# that returns raises StopIteration with the value, and an exception not
# handled propagates and closes the generator. A value that is no exception
# raises TypeError and leaves the generator at its yield, while an error
# instantiating a class is itself thrown in; a created or
# closed generator raises the exception, and a running one ValueError.
# Handlers that loop run in function statements as at module level. The
# exception thrown takes as context the one the generator handles at its
# yield, never one its caller handles, and again, leaving a delegate, the
# one each yield from handles.
from harness import *

log = []

def spin():
    for _ in range(2): pass

def g():
    try:
        x = yield 1
        log.append(("sent", x))
    except ValueError as e:
        spin()
        log.append(("caught", repr(e), repr(e.__context__)))
        yield 2
    try:
        yield 3
    except KeyError:
        spin()
        return "returned"

def statement():
    try:
        yield
    except ValueError:
        spin()
        yield "statement"

def outer():
    got = yield from g()
    log.append(("delegated", got))
    yield "after"

def handling():
    try:
        raise OSError("own")
    except OSError:
        try:
            yield 1
        except ValueError as e:
            spin()
            yield repr(e.__context__)

def bare():
    yield 1

def chained():
    try:
        raise OSError("outer")
    except OSError:
        yield from bare()

class Endless:
    def __iter__(self): return self
    def __next__(self): return 1

def throwless():
    try:
        raise OSError("iterator")
    except OSError:
        yield from Endless()

def unchained():
    yield from bare()

def context(it):
    try:
        raise IndexError("i")
    except IndexError:
        try:
            return it.throw(ValueError)
        except ValueError as e:
            return repr(e.__context__)

def selfish():
    yield me.throw(ValueError)

class Bad(Exception):
    def __new__(cls): return 1

class Failing(Exception):
    def __init__(self): raise KeyError("init")

def catcher():
    try:
        yield 1
    except Exception as e:
        log.append(("thrown", type(e).__name__))
        yield 2

def error(f, *args):
    try:
        return f(*args)
    except BaseException as e:
        return type(e).__name__, str(e)

def throws():
    global me
    del log[:]
    it = g(); next(it)
    out = [it.throw(ValueError("v")), next(it), error(it.throw, KeyError)]
    it = g(); next(it)
    out += [error(it.throw, TypeError("t")), it.gi_frame, error(next, it)]
    it = g(); next(it)
    out += [error(it.throw, 1), it.send("s")]
    it = g(); next(it)
    out += [error(it.throw, Bad), it.gi_frame]
    it = catcher(); next(it)
    out.append(it.throw(Failing))
    it = statement(); next(it)
    out.append(it.throw(ValueError))
    it = outer(); next(it)
    out += [it.throw(ValueError), next(it), it.throw(KeyError)]
    it = g(); next(it)
    out.append(context(it))
    it = handling(); next(it)
    out += [context(it), context(handling()), context(it)]
    it = chained(); next(it)
    out.append(context(it))
    it = unchained(); next(it)
    out.append(context(it))
    it = throwless(); next(it)
    out.append(context(it))
    out += [error(g().throw, ValueError("created")), error(it.throw, OSError)]
    it.close()
    out.append(error(it.throw, OSError("closed")))
    me = selfish()
    out.append(error(next, me))
    out.append(list(log))
    return out

expected = [2, 3, ("StopIteration", "returned"),
            ("TypeError", "t"), None, ("StopIteration", ""),
            ("TypeError", "exceptions must be classes or instances deriving from BaseException, not int"),
            3, ("TypeError", "calling <class '__main__.Bad'> should have returned an instance of BaseException, not int"),
            None, 2, "statement", 2, 3, "after", 2, "OSError('own')", "None", "ValueError()", "OSError('outer')", "None", "OSError('iterator')",
            ("ValueError", "created"), ("OSError", ""), ("OSError", "closed"),
            ("ValueError", "generator already executing"),
            [("caught", "ValueError('v')", "None"), ("sent", "s"), ("thrown", "KeyError"),
             ("caught", "ValueError()", "None"), ("delegated", "returned"),
             ("caught", "ValueError()", "None")]]

def main():
    return throws()

assert_eq(main(), expected)
assert_eq(throws(), expected)
