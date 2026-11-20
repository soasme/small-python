# spec: PLS-315 13.16.3, 27.2.2
# description: A yield from whose delegate generator ended (closed from
# outside) takes the next send, throw or close as one of an iterator
# that is exhausted: a send ends the delegation with None, a throw raises
# at the yield from (an exception the throw refuses there too, but a
# GeneratorExit's refused traceback raises at the caller), a close
# raises GeneratorExit there, and a dead generator so suspended is closed
# the same way. A GeneratorExit class given a value, thrown into a yield
# from of a builtin iterator or an ended generator, is made of it.
from harness import assert_eq

log = []
def inner():
    try:
        yield 1
        yield 2
    finally:
        log.append("inner done")
def deleg(it):
    try:
        r = yield from it
        log.append(("returned", r))
        yield "after"
    except BaseException as e:
        log.append(("deleg", type(e).__name__))
        raise
    finally:
        log.append("deleg done")
def outer(it):
    try:
        yield from it
    except TypeError:
        yield "outer caught"
def setup(depth):
    i = inner()
    g = deleg(i) if depth == 1 else outer(deleg(i))
    next(g); i.close(); del log[:]
    return g
def run(depth, op):
    g = setup(depth)
    try: r = op(g)
    except BaseException as e: r = (type(e).__name__, str(e)[:30])
    out = (r, g.gi_frame is not None, list(log)); del log[:]
    return out

assert_eq(run(1, next), ('after', True, [('returned', None)]))
assert_eq(run(1, lambda g: g.send(5)), ('after', True, [('returned', None)]))
assert_eq(run(1, lambda g: g.throw(KeyError)), (('KeyError', ''), False, [('deleg', 'KeyError'), 'deleg done']))
assert_eq(run(1, lambda g: g.throw(1)), (('TypeError', 'exceptions must be classes or '), False, [('deleg', 'TypeError'), 'deleg done']))
assert_eq(run(1, lambda g: g.throw(KeyError("k"), 1)), (('TypeError', 'instance exception may not hav'), False, [('deleg', 'TypeError'), 'deleg done']))
assert_eq(run(1, lambda g: g.throw(GeneratorExit, 1, 2)), (('TypeError', 'throw() third argument must be'), True, []))
assert_eq(run(1, lambda g: g.close()), (None, False, [('deleg', 'GeneratorExit'), 'deleg done']))
assert_eq(run(1, list), (['after'], False, [('returned', None), 'deleg done']))
assert_eq(run(2, next), ('after', True, [('returned', None)]))
assert_eq(run(2, lambda g: g.throw(1)), ('outer caught', True, [('deleg', 'TypeError'), 'deleg done']))
assert_eq(run(2, lambda g: g.throw(KeyError)), (('KeyError', ''), False, [('deleg', 'KeyError'), 'deleg done']))
assert_eq(run(2, lambda g: g.close()), (None, False, [('deleg', 'GeneratorExit'), 'deleg done']))

def dropped():
    g = setup(1)
    del g
    out = list(log); del log[:]
    return out
assert_eq(dropped(), [('deleg', 'GeneratorExit'), 'deleg done'])

class Exit(GeneratorExit):
    def __init__(self, *args):
        log.append(("made", args))
        super().__init__(*args)
def plain(it):
    yield from it
def late(kind, *args):
    i = inner()
    g = plain(i if kind == "ended" else iter([1, 2])); next(g)
    if kind == "ended": i.close()
    del log[:]
    try: g.throw(*args)
    except BaseException as e: r = (type(e).__name__, e.args)
    out = (r, list(log)); del log[:]
    return out
for kind in ("ended", "iter"):
    assert_eq(late(kind, Exit, (4, 5)), (('Exit', (4, 5)), [('made', (4, 5))]))
    assert_eq(late(kind, Exit, 7), (('Exit', (7,)), [('made', (7,))]))
    assert_eq(late(kind, Exit), (('Exit', ()), [('made', ())]))
