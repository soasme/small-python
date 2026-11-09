# spec: PLS-315 27.2.4, 27.2.3, 28.3, 9.7
# description: A suspended generator whose last reference goes is closed
# before the next statement runs, also when it is suspended in an except
# handler, whose exception's traceback reaches the generator's own frame, or
# when its locals hold that frame; one whose suspended expression holds it is
# closed by a collection while its frame survives, as is one whose locals
# hold the generator itself, and a finished one whose name holds it is
# reclaimed. A generator's frame is one object while it
# runs and is suspended, and outlives it with its code, line and locals, no
# longer naming the generator; its repr names its code, inside functions as at module level.
from harness import *

log = []

def handler(tag):
    try:
        raise KeyError(tag)
    except KeyError:
        try:
            yield 1
        finally:
            log.append(tag + " closed")

def holder():
    me = yield
    try:
        yield me is not None
    finally:
        log.append("holder closed")

def selfish():
    me = None
    try:
        me = yield
        yield
    finally:
        log.append("selfish closed")

def cyclic():
    try:
        [box.pop(), (yield 1)]
    finally:
        log.append("cyclic closed")

class Name(str): pass

def plain():
    yield 1

def raiser():
    x = 5
    yield 1
    raise ValueError("v")

def running():
    yield current.gi_frame

def results():
    global current
    del log[:]
    current = running()
    out = [next(current) is current.gi_frame]
    g = handler("a"); next(g); del g
    log.append("after a")
    g = handler("b"); next(g); g = None
    log.append("after b")
    g = holder(); next(g)
    out.append(g.send(g.gi_frame))
    del g
    log.append("after holder")
    g = raiser(); next(g)
    suspended = g.gi_frame
    try:
        next(g)
    except ValueError as e:
        frame = e.__traceback__.tb_next.tb_frame
    out += [frame is suspended, g.gi_frame]
    del g, suspended
    out += [frame.f_generator, frame.f_code.co_name, frame.f_locals["x"], frame.f_lineno - frame.f_code.co_firstlineno]
    global box
    g = cyclic(); box = [g]; next(g)
    kept = g.gi_frame
    del g
    log.append("before collect")
    host.collect()
    g = plain(); g.__name__ = Name("named"); g.__name__.owner = g
    ended = g.gi_frame
    list(g)
    del g
    host.collect()
    out += [ended.f_generator, ended.f_code.co_name, repr(ended).startswith("<frame at "), repr(ended).endswith("code plain>"), box, kept.f_generator, kept.f_code.co_name, kept.f_lineno - kept.f_code.co_firstlineno]
    g = selfish(); next(g); g.send(g)
    held = g.gi_frame
    del g
    host.collect()
    log.append("after selfish")
    out += [held.f_generator is None, held.f_code.co_name, type(held.f_locals["me"]).__name__]
    out.append(list(log))
    return out

expected = [True, True, True, None, None, "raiser", 5, 3,
            None, "plain", True, True, [], None, "cyclic", 4, True, "selfish", "generator",
            ["a closed", "after a", "b closed", "after b", "holder closed", "after holder",
             "before collect", "cyclic closed", "selfish closed", "after selfish"]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
