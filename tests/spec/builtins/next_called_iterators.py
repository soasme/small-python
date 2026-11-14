# spec: PLS-315 19.3.27, 27.1.5, 27.1.6, 27.1.7
# description: next() of an iterator or reversed object over an instance
# calls its __getitem__, and of a map or filter calls its function, each of
# which may call others or not; an IndexError ends the first two, a
# StopIteration from any gives the default when one is passed, and other
# exceptions propagate; an exhausted iterator stays so; inside functions as
# at module level.
from harness import *

log = []

class Seq:
    def __getitem__(self, i):
        for _ in range(1): pass
        log.append(i)
        if i == 2: raise IndexError(i)
        if i == "k": raise KeyError(i)
        return i

class Sized(Seq):
    def __len__(self): return 2

class Bad(Seq):
    def __getitem__(self, i):
        log.append(("bad", i))
        raise KeyError(i)

class BadSized(Bad):
    def __len__(self): return 1

def double(x):
    for _ in range(1): pass
    log.append(("f", x))
    if x == "stop": raise StopIteration
    if x == "key": raise KeyError(x)
    return x * 2

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def calls():
    del log[:]
    it, r = iter(Seq()), reversed(Sized())
    out = [next(it), next(it), next(it, "d"), next(it, "e"), error(lambda: next(it))]
    out += [next(r), next(r), next(r, "d")]
    out.append(error(lambda: next(iter(Bad()), 0)))
    out.append(error(lambda: next(reversed(BadSized()), 0)))
    m, f = map(double, [1, "stop", 3]), filter(double, [0, 4])
    out += [next(m), next(m, "d"), next(m), next(m, "e"), next(f), next(f, "g")]
    out.append(error(lambda: next(map(double, ["key"]), 0)))
    out.append(error(lambda: next(map(double, ["stop"]))))
    out.append(list(log))
    return out

expected = [0, 1, "d", "e", ("StopIteration", ""), 1, 0, "d", ("KeyError", "0"), ("KeyError", "0"),
            2, "d", 6, "e", 4, "g", ("KeyError", "'key'"), ("StopIteration", ""),
            [0, 1, 2, 1, 0, ("bad", 0), ("bad", 0), ("f", 1), ("f", "stop"), ("f", 3), ("f", 0), ("f", 4),
             ("f", "key"), ("f", "stop")]]
assert_eq(calls(), expected)
assert_eq(calls(), expected)
log.clear()
it = iter(Seq())
assert_eq([next(it), next(map(double, [5])), next(filter(double, [0]), "n")], [0, 10, "n"])
assert_eq(log, [0, ("f", 5), ("f", 0)])
