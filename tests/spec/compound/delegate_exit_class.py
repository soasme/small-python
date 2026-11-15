# spec: PLS-315 13.16.3, 27.2.2
# description: throw() of GeneratorExit, or of a subclass made without
# Python code, into a generator suspended in a yield from closes the
# delegates innermost first, an instance's Python close too, then raises
# an instance of the class at each yield from outward: finally clauses
# run in that order, throw() raises the instance, or returns a value a
# frame yields after catching it, and an error from a delegate's close
# raises at the yield from instead. Inside functions as at module level.
from harness import *

log = []

class Exit(GeneratorExit): pass

class Closing:
    def __init__(self, bad): self.bad = bad
    def __iter__(self): return self
    def __next__(self):
        for _ in range(2): pass
        return "item"
    def close(self):
        for _ in range(2): pass
        log.append("instance close")
        if self.bad: raise KeyError("close")

def inner(source):
    try:
        yield from source
    finally:
        log.append("inner finally")

def outer(source, keeps=False):
    try:
        yield from inner(source)
    except GeneratorExit as e:
        log.append(("outer caught", type(e).__name__))
        if keeps:
            yield "kept"
        raise
    finally:
        log.append("outer finally")

def thrown(g, k):
    next(g)
    try:
        return ("value", g.throw(k))
    except BaseException as e:
        return type(e).__name__, type(e.__context__).__name__

def results():
    del log[:]
    return [thrown(outer(iter([1, 2])), GeneratorExit), thrown(outer(Closing(False)), Exit),
            thrown(outer(Closing(True)), GeneratorExit), thrown(outer(iter([1]), True), Exit), list(log)]

expected = [("GeneratorExit", "NoneType"), ("Exit", "NoneType"), ("KeyError", "NoneType"), ("value", "kept"),
            ["inner finally", ("outer caught", "GeneratorExit"), "outer finally",
             "instance close", "inner finally", ("outer caught", "Exit"), "outer finally",
             "instance close", "inner finally", "outer finally",
             "inner finally", ("outer caught", "Exit"), "outer finally"]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
