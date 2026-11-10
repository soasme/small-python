# spec: PLS-315 27.2.4, 9.7
# description: A suspended generator that becomes unreachable at a yield
# inside a try, a with or an except handler is closed before the code after
# it goes on, also in the middle of an expression: its finally clauses and
# __exit__ calls run, an exception escaping them or a yield in them leaves
# the program running, and catching GeneratorExit to return ends it; one
# dropped while another is closing is closed too, inside functions as at
# module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

def gen(tag):
    try:
        yield 1
    finally:
        spin()
        log.append(tag)

class Manager:
    def __enter__(self): return self
    def __exit__(self, *exc):
        spin()
        log.append(("exit", exc[0].__name__))

def managed():
    with Manager():
        yield 1

def handled():
    try:
        raise KeyError("k")
    except KeyError:
        try:
            yield 1
        finally:
            spin()
            log.append("handled")

def returning():
    try:
        yield 1
    except GeneratorExit:
        spin()
        log.append("returning")
        return 5

def bad():
    try:
        yield 1
    finally:
        spin()
        log.append("bad")
        1 / 0

def stubborn():
    try:
        yield 1
    finally:
        spin()
        log.append("stubborn")
        yield 2

def outer():
    g = gen("inner"); next(g)
    try:
        yield 1
    finally:
        spin()
        del g
        log.append("outer")

def started(g):
    next(g)
    return g

def results():
    del log[:]
    out = []
    g = started(gen("a")); del g
    out.append(list(log))
    box = [started(gen("mid"))]
    out.append([box.pop() and None, list(log), 3 + 4])
    g = started(managed()); g = None
    g = started(handled()); g = None
    g = started(returning()); g = None
    g = started(bad()); g = None
    out.append("after bad")
    g = started(stubborn()); g = None
    out.append("after stubborn")
    g = started(outer()); g = None
    out.append(sorted(log[-2:]))
    out.append(log[:-2])
    return out

expected = [["a"], [None, ["a", "mid"], 7], "after bad", "after stubborn", ["inner", "outer"],
            ["a", "mid", ("exit", "GeneratorExit"), "handled", "returning", "bad", "stubborn"]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
box = [started(gen("top"))]
assert_eq([box.pop() and None, log[-1]], [None, "top"])
g = started(bad()); g = None
assert_eq(log[-1], "bad")
