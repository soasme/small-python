# spec: PLS-315 27.2.4
# description: Suspended generators that become unreachable together, some
# at a yield outside any handler and some inside a try or an except
# handler, are each closed before the code after them goes on, in the
# order they become unreachable: the finally clauses, which may loop, run
# whatever generators that close running nothing come before them, and
# one that raises leaves the program running. Inside functions as at
# module level.
from harness import *

log = []

def plain(tag):
    yield tag

def guarded(tag):
    try:
        yield tag
    finally:
        for _ in range(2): pass
        log.append(tag)

def handled(tag):
    try:
        yield 1
        raise KeyError(tag)
    except KeyError:
        try:
            yield 2
        finally:
            log.append("handled " + tag)

def failing():
    try:
        yield 1
    finally:
        raise LookupError("ignored")

def drop():
    a = plain("a"); next(a)
    b = guarded("b"); next(b)
    c = plain("c"); next(c)
    h = handled("h"); next(h); next(h)
    f = failing(); next(f)
    d = guarded("d"); next(d)
    return "dropped"

def rebind():
    g = plain("p"); next(g)
    g = guarded("q"); next(g)
    g = plain("r"); next(g)
    g = guarded("s"); next(g)
    g = None
    log.append("after")

def results():
    out = [drop(), log[:]]
    del log[:]
    rebind()
    out.append(log[:])
    del log[:]
    out.append([x for x in (plain(1), guarded("t"), plain(2)) if next(x) and False] or log[:])
    del log[:]
    return out

expected = ['dropped', ['d', 'handled h', 'b'], ['q', 's', 'after'], ['t']]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
