# spec: PLS-315 16.4.1, 16.6.2, 16.6.3
# description: A class body with annotations that calls and loops runs its
# statements in order: its annotated assignments assign, its annotations
# stay unevaluated until __annotations__ is read, and an exception from a
# call propagates and makes no class, inside functions as at module level.
from harness import *

log = []

def note(x):
    for _ in range(2): pass
    log.append(x)
    return x

def results():
    del log[:]
    class Annotated:
        first: note("first annotation") = note(1)
        for i in range(2):
            note(i)
        later: Later
        last: int = sorted([note(3), 2], reverse=True)[0]
    before = list(log)
    Later = str
    out = [before, Annotated.first, Annotated.last, hasattr(Annotated, "later"), Annotated.i]
    out.append(Annotated.__annotations__)
    out.append(log[len(before):])
    try:
        class Broken:
            value: int = note(5)
            note(1 // 0)
        out.append("made")
    except ZeroDivisionError:
        out.append("Broken" in locals())
    return out

expected = [[1, 0, 1, 3], 1, 3, False, 1, {"first": "first annotation", "later": str, "last": int},
            ["first annotation"], False]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
