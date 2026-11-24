# spec: PLS-315 7.7.7, 26.1.2
# description: reversed() of a sequence calls its Python __len__, which may
# loop, once; list() and list.extend, which size their result by
# LengthHint, of an instance of a reversed subclass not defining
# __length_hint__ call reversed's own, which calls that __len__ again
# before iterating, as an explicit call does, while tuple() does not; an
# exception from __len__ propagates.
from harness import *

log = []
def spin():
    for _ in range(2): pass
class Seq:
    def __init__(self, fail=None): self.fail = fail
    def __len__(self):
        spin(); log.append("len")
        if self.fail: raise self.fail("len")
        return 3
    def __getitem__(self, i):
        if i < 3: return i
        raise IndexError
class R(reversed): pass

def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def cases():
    def extend():
        l = [9]; l.extend(R(Seq())); return l
    return [run(lambda: list(R(Seq()))), run(lambda: tuple(R(Seq()))), run(extend),
            run(lambda: list(R(Seq(LookupError)))), run(lambda: R(Seq()).__length_hint__())]
expected = [([2, 1, 0], ["len", "len"]), ((2, 1, 0), ["len"]), ([9, 2, 1, 0], ["len", "len"]),
            (("LookupError", "len"), ["len"]), (3, ["len", "len"])]
assert_eq(cases(), expected)
assert_eq(cases(), expected)
