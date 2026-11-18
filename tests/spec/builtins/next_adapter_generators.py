# spec: PLS-315 19.3.27, 27.1.4, 27.1.6, 27.1.8
# description: next() of a zip, map, enumerate or filter over a generator
# resumes the generator, which may loop, for each item; when the
# generator returns a value other than None, the StopIteration that ends
# the adapter carries it, and the next call raises a bare StopIteration;
# next() with a default returns the default instead. An error from the
# generator propagates. Inside functions as at module level.
from harness import *

log = []

def gen(name, *items, ret=None):
    for item in items:
        for _ in range(2): pass
        log.append((name, item))
        yield item
    return ret

def bad():
    yield 1
    raise KeyError("k")

def run(f):
    del log[:]
    try:
        r = f()
    except StopIteration as e:
        r = ("StopIteration", e.args)
    except KeyError as e:
        r = ("KeyError", str(e))
    return r, list(log)

def results():
    out = []
    z = zip(gen("a", 1, 2), gen("b", 3), (9, 9, 9))
    out += [run(lambda: next(z)), run(lambda: next(z)), run(lambda: next(z)), run(lambda: next(z, "d"))]
    z = zip(gen("c", 1, ret=5), "xy")
    out += [run(lambda: next(z)), run(lambda: next(z)), run(lambda: next(z, "dflt"))]
    m = map(abs, gen("m", -1, ret=7))
    out += [run(lambda: next(m)), run(lambda: next(m)), run(lambda: next(m))]
    z = zip("ab", gen("e", 1, ret=6))
    out += [run(lambda: next(z)), run(lambda: next(z)), run(lambda: z.__next__())]
    z = zip(bad(), "abc")
    out += [run(lambda: next(z)), run(lambda: next(z)), run(lambda: next(z))]
    e = enumerate(gen("h", 1, ret=8), 5)
    out += [run(lambda: next(e)), run(lambda: next(e)), run(lambda: next(e, "d"))]
    f = filter(None, gen("i", 0, 1, ret=4))
    out += [run(lambda: next(f)), run(lambda: next(f))]
    return out

expected = [((1, 3, 9), [("a", 1), ("b", 3)]), (("StopIteration", ()), [("a", 2)]), (("StopIteration", ()), []), ("d", []),
            ((1, "x"), [("c", 1)]), (("StopIteration", (5,)), []), ("dflt", []),
            (1, [("m", -1)]), (("StopIteration", (7,)), []), (("StopIteration", ()), []),
            (("a", 1), [("e", 1)]), (("StopIteration", (6,)), []), (("StopIteration", ()), []),
            ((1, "a"), []), (("KeyError", "'k'"), []), (("StopIteration", ()), []),
            ((5, 1), [("h", 1)]), (("StopIteration", (8,)), []), ("d", []),
            (1, [("i", 0), ("i", 1)]), (("StopIteration", (4,)), [])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
