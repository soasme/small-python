# spec: PLS-315 24.1.1, 7.7.7
# description: bytearray.extend() of an iterable instance calls its
# __iter__, which may loop, then its length hint, then takes its items in
# order, each converted by __index__, and appends them at the array's end
# once all are taken: a change __iter__ or a generator makes to the array
# comes first, and an error leaves it as it was. A TypeError getting the
# iterator becomes "can't extend bytearray with". Inside functions as at
# module level.
from harness import *

log = []
class It:
    def __init__(self, items, target=None): self.items, self.target = items, target
    def __iter__(self):
        for _ in (): pass
        log.append("iter")
        if self.target is not None: self.target.extend(b"!")
        return iter(self.items)
    def __len__(self):
        for _ in (): pass
        log.append("len"); return 1
def gen(b):
    yield 1
    b.append(50)
    yield 2
def extends():
    del log[:]
    b = bytearray(b"x")
    out = [b.extend(It([65, 66])), bytes(b)]
    out.append(b.extend(It([67], b))); out.append(bytes(b))
    out.append(b.extend(gen(b))); out.append(bytes(b))
    try: b.extend(It([1, 300]))
    except ValueError as e: out.append(str(e))
    out.append(bytes(b))
    class R:
        def __iter__(self):
            for _ in (): pass
            return 3
    try: b.extend(R())
    except TypeError as e: out.append(str(e))
    out.append(log)
    return out

expected = [None, b"xAB", None, b"xAB!C", None, b"xAB!C2\x01\x02", "byte must be in range(0, 256)", b"xAB!C2\x01\x02",
            "can't extend bytearray with R", ["iter", "len", "iter", "len", "iter", "len"]]
assert_eq(extends(), expected)

def nested():
    return extends()

assert_eq(nested(), expected)
