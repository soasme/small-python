# spec: PLS-315 19.3.31
# description: print's file may be any object with a write attribute, such
# as a class whose write and flush are builtin methods: print writes each
# part through write, then calls flush with no arguments only when flush is
# true; an error from flush propagates after every write is done.
from harness import *

log = []

class Builtin:
    write = log.append
    flush = log.reverse

class Failing:
    write = log.append
    flush = [].pop

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    print("a", "b", file=Builtin, flush=True)
    first = list(log)
    print("c", file=Builtin)
    out = [first, list(log), error(lambda: print("d", file=Failing, flush=True)), list(log)]
    return out

expected = [["\n", "b", " ", "a"], ["\n", "b", " ", "a", "c", "\n"], ("IndexError", "pop from empty list"),
            ["\n", "b", " ", "a", "c", "\n", "d", "\n"]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
