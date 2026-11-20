# spec: PLS-315 10.3, 7.3.2, 7.5.1
# description: A class defining __bool__ by a descriptor whose read raises
# AttributeError has no __bool__ for truth: its truth is that of what its
# __len__ returns, unchecked as a length, or true when the __len__ read
# also raises AttributeError; another error of either read propagates.
# bool(), not, a conditional, and, a test in a chain and filter agree,
# on the machine as in a plain expression, each read and call made once.
from harness import *

log = []
def booh(self): raise AttributeError("booh")
def boom(self): raise KeyError("boom")
def getter(n):
    def get(self):
        log.append("get")
        return lambda: n
    return property(get)
def length(n):
    def __len__(self):
        for _ in (): pass
        log.append(n)
        return n
    return __len__

cases = [length(0), length(3), property(booh), getter(0), length(-1), property(boom), length("x"), length([])]
classes = [type("C%d" % i, (), {"__bool__": property(booh), "__len__": f}) for i, f in enumerate(cases)]

def attempt(f):
    try: return f()
    except Exception as e: return type(e).__name__

def machine(x):
    for _ in (): pass
    out = [attempt(lambda: bool(x))]
    try: out.append(not x)
    except Exception as e: out.append(type(e).__name__)
    try: out.append(1 if x else 0)
    except Exception as e: out.append(type(e).__name__)
    try: out.append(1 < 2 < 3 if x else 9)
    except Exception as e: out.append(type(e).__name__)
    try: out.append([y for y in [x] if y] == [x])
    except Exception as e: out.append(type(e).__name__)
    out.append(attempt(lambda: list(filter(None, [x])) == [x]))
    return out

def plain(x):
    return [attempt(lambda: bool(x)), attempt(lambda: not x), attempt(lambda: 1 if x else 0), attempt(lambda: 1 < 2 < 3 if x else 9)]

def results():
    del log[:]
    out = [(machine(k()), plain(k())) for k in classes]
    return out, list(log)

T = [True, False, 1, True, True, True]
F = [False, True, 0, 9, False, False]
K = ["KeyError"] * 6
expected = ([(F, F[:4]), (T, T[:4]), (T, T[:4]), (F, F[:4]), (T, T[:4]), (K, K[:4]), (T, T[:4]), (F, F[:4])],
            [0] * 10 + [3] * 10 + ["get"] * 10 + [-1] * 10 + ["x"] * 10 + [[]] * 10)

assert_eq(results(), expected)
assert_eq(results(), expected)
