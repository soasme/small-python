# spec: PLS-315 13.16.3, 27.2.2
# description: A throw whose arguments are refused (no exception, an
# instance given a value, a traceback that is none) raises its TypeError
# where a generator checks them: at the yield from waiting on the
# innermost generator, which stays suspended, chained to the exception
# handled there; at the caller when that generator is the thrown one; an
# iterator instance's Python throw receives them as given, the generators
# delegating to it running meanwhile, its error raising at the yield from
# waiting on it. A
# GeneratorExit closes the yield from's delegate first, whose own error
# then raises at the yield from instead; the generator is executing
# meanwhile.
from harness import *

log = []
class It:
    def __init__(self, fail=False): self.fail = fail
    def __iter__(self): return self
    def __next__(self): return 1
    def throw(self, *args):
        log.append(("throw", repr(args)))
        if self.fail: raise KeyError("from throw")
        return "thrown"
    def close(self):
        log.append("close")
        if self.fail: raise KeyError("from close")
class Ender(It):
    # Its close tries to close the generator delegating to it, which is
    # executing, so that the close fails.
    def close(self):
        log.append("close")
        if self.fail:
            self.fail = False
            self.owner.close()
class Watcher(It):
    # Its throw sees the generators delegating to it running.
    def throw(self, *args):
        log.append(("running", self.owner.gi_running, self.outer.gi_running))
        return super().throw(*args)
def watched():
    it = Watcher()
    g = plain(owned(it))
    it.outer = g
    return g
def owned(it):
    g = deleg(it)
    it.owner = g
    return g
class Bare:
    def __iter__(self): return self
    def __next__(self): return 1
def inner():
    try:
        yield 1
    finally:
        log.append("inner done")
def stubborn():
    try:
        yield 1
    except GeneratorExit:
        yield "ignored"
def deleg(it):
    try:
        yield from it
    except TypeError as e:
        log.append(("caught", str(e)[:20]))
        yield "caught"
def plain(it):
    yield from it
def handling(it):
    try:
        raise ValueError("v")
    except ValueError:
        try:
            yield from it
        except TypeError as e:
            log.append(("context", type(e.__context__).__name__))
            yield "context"
async def awaiting(g):
    try:
        return await g
    except TypeError as e:
        log.append(("awaited", str(e)[:20]))
        return "awaited"
class Await:
    def __init__(self, it): self.it = it
    def __await__(self): return (yield from self.it)
def run(g, *args):
    del log[:]
    g.send(None)
    try: r = g.throw(*args)
    except BaseException as e: r = (type(e).__name__, str(e)[:24])
    frame = g.gi_frame if hasattr(g, "gi_frame") else g.cr_frame
    out = (r, frame is not None, list(log))
    del log[:]
    return out
def direct(kind):
    # A direct call, not a starred one, the generator executing while
    # its delegate closes.
    del log[:]
    it = Ender(True) if kind == "ender" else It()
    g = owned(it)
    next(g)
    try:
        if kind == "value": r = g.throw(KeyError("k"), 1)
        elif kind == "none": r = g.throw(1)
        else: r = g.throw(GeneratorExit, 1, 2)
    except BaseException as e: r = (type(e).__name__, str(e)[:24])
    return r, g.gi_frame is not None, list(log)
def inside():
    yield run(deleg(inner()), 1)
    yield run(plain(deleg(It()), ), 1)
    yield run(deleg(inner()), GeneratorExit, 1, 2)
assert_eq(run(inner(), 1), (('TypeError', 'exceptions must be class'), True, []))
assert_eq(run(inner(), KeyError('k'), 1), (('TypeError', 'instance exception may n'), True, []))
assert_eq(run(inner(), KeyError, 1, 2), (('TypeError', 'throw() third argument m'), True, []))
assert_eq(run(deleg(inner()), 1), ('caught', True, [('caught', 'exceptions must be c')]))
assert_eq(run(deleg(inner()), KeyError('k'), 1), ('caught', True, [('caught', 'instance exception m')]))
assert_eq(run(deleg(inner()), KeyError, None, 2), ('caught', True, [('caught', 'throw() third argume')]))
assert_eq(run(plain(deleg(inner())), 1), ('caught', True, [('caught', 'exceptions must be c')]))
assert_eq(run(plain(plain(inner())), 'x'), (('TypeError', 'exceptions must be class'), False, ['inner done']))
assert_eq(run(deleg(plain(inner())), [1]), ('caught', True, [('caught', 'exceptions must be c')]))
assert_eq(run(handling(inner()), 1), ('context', True, [('context', 'ValueError')]))
assert_eq(run(handling(plain(inner())), KeyError(), 0), ('context', True, [('context', 'ValueError')]))
assert_eq(run(deleg(It()), 1), ('thrown', True, [('throw', '(1,)')]))
assert_eq(run(deleg(It()), 'text'), ('thrown', True, [('throw', "('text',)")]))
assert_eq(run(deleg(It()), KeyError, 1, 2), ('thrown', True, [('throw', "(<class 'KeyError'>, 1, 2)")]))
assert_eq(run(deleg(It(True)), KeyError('k'), 1), (('KeyError', "'from throw'"), False, [('throw', "(KeyError('k'), 1)")]))
assert_eq(run(plain(deleg(It(True))), KeyError('k'), 1), (('KeyError', "'from throw'"), False, [('throw', "(KeyError('k'), 1)")]))
assert_eq(run(plain(plain(It(True))), 2, 3), (('KeyError', "'from throw'"), False, [('throw', '(2, 3)')]))
assert_eq(run(watched(), KeyError('k'), 1), ('thrown', True, [('running', True, True), ('throw', "(KeyError('k'), 1)")]))
assert_eq(run(deleg(It(True)), 1), (('KeyError', "'from throw'"), False, [('throw', '(1,)')]))
assert_eq(run(plain(deleg(It(True))), None), (('KeyError', "'from throw'"), False, [('throw', '(None,)')]))
assert_eq(run(deleg(Bare()), 1), (('TypeError', 'exceptions must be class'), True, []))
assert_eq(run(plain(deleg(Bare())), KeyError('k'), 1), (('TypeError', 'instance exception may n'), False, []))
assert_eq(run(deleg(iter([1, 2])), 1), (('TypeError', 'exceptions must be class'), True, []))
assert_eq(run(plain(deleg(iter([1, 2]))), 1), (('TypeError', 'exceptions must be class'), False, []))
assert_eq(run(deleg(inner()), GeneratorExit, 1, 2), (('TypeError', 'throw() third argument m'), True, ['inner done']))
assert_eq(run(deleg(It()), GeneratorExit, None, 2), (('TypeError', 'throw() third argument m'), True, ['close']))
assert_eq(run(deleg(It(True)), GeneratorExit, 1, 2), (('KeyError', "'from close'"), False, ['close']))
assert_eq(run(deleg(stubborn()), GeneratorExit, 1, 2), (('RuntimeError', 'generator ignored Genera'), False, []))
assert_eq(run(deleg(Bare()), GeneratorExit, 1, 2), (('TypeError', 'throw() third argument m'), True, []))
assert_eq(run(owned(Ender(True)), GeneratorExit, 1, 2), (('ValueError', 'generator already execut'), False, ['close']))
assert_eq(run(plain(deleg(inner())), GeneratorExit(), 1), (('TypeError', 'instance exception may n'), True, ['inner done']))
assert_eq(run(awaiting(Await(inner())), 1), (('StopIteration', 'awaited'), False, [('awaited', 'exceptions must be c'), 'inner done']))
assert_eq(run(awaiting(Await(deleg(inner()))), 1), ('caught', True, [('caught', 'exceptions must be c')]))
assert_eq(direct('ender'), (('ValueError', 'generator already execut'), False, ['close']))
assert_eq(direct('exit'), (('TypeError', 'throw() third argument m'), True, ['close']))
assert_eq(direct('value'), ('thrown', True, [('throw', "(KeyError('k'), 1)")]))
assert_eq(direct('none'), ('thrown', True, [('throw', '(1,)')]))
assert_eq(list(inside()), [('caught', True, [('caught', 'exceptions must be c')]), ('thrown', True, [('throw', '(1,)')]), (('TypeError', 'throw() third argument m'), True, ['inner done'])])
