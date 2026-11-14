# spec: PLS-315 7.7.6, 7.7.7, 27.1
# description: list(), sorted(), list.extend(), +=, a starred display item and
# bytes() of an iterator or reversed object over a sequence ask its length
# hint, which calls the sequence's __len__, which may call others or not; a
# TypeError from it is ignored while another exception or a negative length
# propagates, an iterator over a sequence without __len__ gives none, and an
# exhausted one calls nothing; inside functions as at module level.
from harness import *

log = []

class Seq:
    def __init__(self, n, bad=None): self.n, self.bad, self.calls = n, bad, 0
    def __len__(self):
        log.append("len")
        for _ in range(1): pass
        self.calls += 1
        if self.calls > 1 and self.bad: raise self.bad
        if self.calls > 1 and self.n == "neg": return -1
        return 3 if self.n == "neg" else self.n
    def __getitem__(self, i):
        if i >= 3: raise IndexError(i)
        return i

class Quick(Seq):
    def __len__(self):
        log.append("quick")
        return self.n

class Unsized:
    def __getitem__(self, i):
        if i >= 2: raise IndexError(i)
        return i

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def hints():
    del log[:]
    out = [list(reversed(Seq(3))), sorted(reversed(Seq(2))), list(iter(Seq(3))), list(reversed(Quick(2))), list(iter(Unsized()))]
    l = [9]
    l.extend(reversed(Seq(1)))
    out.append(l)
    out.append(error(lambda: list(reversed(Seq(3, TypeError("t"))))))
    out.append(error(lambda: list(reversed(Seq(3, KeyError("k"))))))
    out.append(error(lambda: list(reversed(Seq("neg")))))
    s = Seq(3, KeyError("k"))
    len(s)
    out.append(error(lambda: list(iter(s))))
    l = [1]
    l += reversed(Seq(1))
    out.append([[*reversed(Seq(2))], bytes(iter(Seq(3))), l])
    it = iter(Seq(3))
    out.append(list(it))
    log.append("|")
    out.append(list(it))
    out.append(list(log))
    return out

expected = [[2, 1, 0], [0, 1], [0, 1, 2], [1, 0], [0, 1], [9, 0],
            [2, 1, 0], ("KeyError", "'k'"), ("ValueError", "__len__() should return >= 0"), ("KeyError", "'k'"),
            [[1, 0], b"\x00\x01\x02", [1, 0]], [0, 1, 2], [],
            ["len"] * 5 + ["quick"] * 2 + ["len"] * 16 + ["|"]]
assert_eq(hints(), expected)
assert_eq(hints(), expected)
log.clear()
assert_eq([list(reversed(Seq(2))), list(iter(Seq(1)))], [[1, 0], [0, 1, 2]])
assert_eq(log, ["len", "len", "len"])
