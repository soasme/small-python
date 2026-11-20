# spec: PLS-315 27.1.3
# description: iter(f, sentinel) of a bound method or a callable instance
# with a Python method, which may loop, calls it for each item until it
# returns the sentinel or raises StopIteration, through list(), next(),
# sorted(), tuple(), a comprehension and a generator; another exception
# propagates. Inside functions as at module level.
from harness import *

class C:
    def __init__(self): self.i = 0
    def __call__(self):
        for _ in (): pass
        self.i += 1
        if self.i == 7: raise LookupError("seven")
        return self.i
class K:
    def __init__(self): self.i = 0
    def step(self):
        for _ in (): pass
        self.i += 1
        if self.i > 3: raise StopIteration
        return self.i
def t(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))

def results():
    out = [t(lambda: list(iter(C(), 4))), t(lambda: list(iter(C(), 99))), t(lambda: list(iter(K().step, 99)))]
    it = iter(C(), 3)
    out.append((next(it), next(it), t(lambda: next(it)), t(lambda: next(it))))
    out.append(t(lambda: [x for x in iter(K().step, 2)]))
    def g():
        for x in iter(C(), 5): yield x
    out.append(list(g()))
    out.append((t(lambda: sorted(iter(C(), 4), reverse=True)), t(lambda: tuple(iter(K().step, None)))))
    return out

expected = [[1, 2, 3], ("LookupError", "seven"), [1, 2, 3], (1, 2, ("StopIteration", ""), ("StopIteration", "")),
            [1], [1, 2, 3, 4], ([3, 2, 1], (1, 2, 3))]
assert_eq(results(), expected)
assert_eq(list(iter(C(), 3)), [1, 2])
