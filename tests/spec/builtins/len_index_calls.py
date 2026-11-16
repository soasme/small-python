# spec: PLS-315 7.5.1, 7.5.2, 19.3.24, 27.1.7
# description: len(), bool() and reversed() of an instance whose __len__
# returns an object with a Python __index__ call that __index__, which may
# loop, after __len__, and take its int as the length: a negative one
# raises ValueError, one past a Py_ssize_t OverflowError, an __index__
# returning no int TypeError, and its exception propagates; bool() is the
# length's truth, as are not, and and if. Inside functions as at module
# level.
from harness import *

log = []

class N:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in range(2): pass
        log.append(("index", self.v))
        if self.v == "raise": raise LookupError("i")
        return self.v

class L:
    def __init__(self, v): self.v = v
    def __len__(self):
        log.append("len")
        return N(self.v)

class R(L):
    def __getitem__(self, i): return i * 10

def t(f):
    try:
        r = f()
    except Exception as e:
        r = type(e).__name__ + ": " + str(e)
    out = (r, log[:])
    del log[:]
    return out

def results():
    return [t(lambda: len(L(3))), t(lambda: bool(L(0))), t(lambda: bool(L(2))), t(lambda: len(L(-1))),
            t(lambda: len(L("s"))), t(lambda: len(L("raise"))), t(lambda: [x for x in reversed(R(3))]),
            t(lambda: len(L(2 ** 70))), t(lambda: bool(L(-1))), t(lambda: not L(0)), t(lambda: L(1) and 5),
            t(lambda: "yes" if L(0) else "no")]

expected = [(3, ['len', ('index', 3)]), (False, ['len', ('index', 0)]), (True, ['len', ('index', 2)]),
            ('ValueError: __len__() should return >= 0', ['len', ('index', -1)]),
            ('TypeError: N.__index__() must return an int, not str', ['len', ('index', 's')]),
            ('LookupError: i', ['len', ('index', 'raise')]), ([20, 10, 0], ['len', ('index', 3)]),
            ("OverflowError: cannot fit 'int' into an index-sized integer", ['len', ('index', 1180591620717411303424)]),
            ('ValueError: __len__() should return >= 0', ['len', ('index', -1)]), (True, ['len', ('index', 0)]),
            (5, ['len', ('index', 1)]), ('no', ['len', ('index', 0)])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
