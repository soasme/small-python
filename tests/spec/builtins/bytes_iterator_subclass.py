# spec: PLS-315 26.4.1, 26.4.2, 7.7.7
# description: bytes(), bytearray() and bytearray.extend of an instance of
# a builtin iterator's subclass that overrides neither __iter__ nor
# __next__ iterate it as its iterator does: a reversed one over a sequence
# calls the sequence's Python __getitem__, which may loop, for each item,
# bytes() and bytearray.extend asking its length hint, the sequence's
# Python __len__, first;
# an exception from either propagates, and an item out of range is a
# ValueError.
from harness import *

log = []
def spin():
    for _ in range(2): pass
class Seq:
    def __init__(self, items, fail=None): self.items, self.fail = items, fail
    def __len__(self):
        spin(); log.append("len"); return len(self.items)
    def __getitem__(self, i):
        spin(); log.append(i)
        if i == self.fail: raise LookupError(i)
        return self.items[i]
class R(reversed): pass

def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def cases():
    def extend():
        b = bytearray(b"z"); b.extend(R(Seq([1, 2]))); return b
    return [run(lambda: bytes(R(Seq([65, 66])))), run(lambda: bytearray(R(Seq([67, 68])))), run(extend),
            run(lambda: bytes(R(Seq([1, 2], fail=0)))), run(lambda: bytearray(R(Seq([300]))))]
expected = [(b"BA", ["len", "len", 1, 0]), (bytearray(b"DC"), ["len", 1, 0]), (bytearray(b"z\x02\x01"), ["len", "len", 1, 0]),
            (("LookupError", "0"), ["len", "len", 1, 0]), (("ValueError", "byte must be in range(0, 256)"), ["len", 0])]
assert_eq(cases(), expected)
assert_eq(cases(), expected)
