# spec: PLS-315 13.16.3, 27.1.6
# description: a generator's yield from of a map whose function is
# Python code, or a bound method, which may loop, calls it for each item
# as the generator is resumed, by next(), a loop or a consumer, in order
# with the other side effects; the function's error propagates through
# the generator, and its StopIteration ends the map and the yield from
# with its value. send() of a value other than None still fails on the
# map. Inside functions as at module level.
from harness import *

log = []

def f(x):
    for _ in (): pass
    log.append(x)
    if x == 9: raise StopIteration(77)
    if x == 8: raise KeyError(x)
    return x * 2

class B:
    def m(self, x):
        for _ in (): pass
        return f(x) + 1

def gen(source):
    log.append("start")
    r = yield from source
    log.append("end")
    yield r

def calls():
    out = [list(gen(map(f, [1, 2]))), [x for x in gen(map(f, [3]))], list(gen(map(B().m, [4]))),
           list(gen(map(f, [5, 9, 6]))), list(gen(map(lambda a, b: a + b, [1, 2], [10, 20, 30])))]
    for x in gen(map(f, [7])):
        log.append(("got", x))
    g = gen(map(f, [1, 2]))
    out.append((next(g), next(g)))
    try: g.send(3)
    except AttributeError as e: out.append(str(e))
    try: list(gen(map(f, [1, 8, 2])))
    except KeyError as e: out.append(e.args)
    return out

expected = [[2, 4, None], [6, None], [9, None], [10, 77], [11, 22, None], (2, 4), "'map' object has no attribute 'send'", (8,)]
expected_log = ["start", 1, 2, "end", "start", 3, "end", "start", 4, "end", "start", 5, 9, "end", "start", "end",
                "start", 7, ("got", 14), "end", ("got", None), "start", 1, 2, "start", 1, 8]
assert_eq(calls(), expected)
assert_eq(log, expected_log)
log.clear()
assert_eq(calls(), expected)
assert_eq(log, expected_log)
log.clear()

g = gen(map(f, [3, 4]))
assert_eq((list(g), log), ([6, 8, None], ["start", 3, 4, "end"]))
