# spec: PLS-315 25.1.1, 24.1.1, 7.7.7
# description: bytes() and bytearray() of an iterable instance call its
# __iter__, which may loop, then, for bytes() only, its length hint, then
# take its items in order, each converted by __index__; a generator, map or
# other iterator is consumed alike. A TypeError getting the iterator
# becomes "cannot convert"; other errors, and an item's range or type
# error, propagate. Inside functions as at module level.
from harness import *

log = []

class Items:
    def __init__(self, items): self.items = items
    def __iter__(self):
        for _ in range(2): pass
        log.append("iter")
        return iter(self.items)
    def __len__(self):
        for _ in range(2): pass
        log.append("len")
        return len(self.items)

class Refused:
    def __iter__(self):
        for _ in range(2): pass
        return 5

class Raising:
    def __init__(self, error): self.error = error
    def __iter__(self):
        for _ in range(2): pass
        raise self.error

def gen(n):
    for i in range(n):
        log.append(i)
        yield i + 97

def error(f, *args):
    try:
        return f(*args)
    except Exception as e:
        return type(e).__name__, str(e)

def made():
    del log[:]
    out = [bytes(Items([104, 105])), bytearray(Items((1, 2))), list(log)]
    del log[:]
    out += [bytes(gen(2)), bytearray(gen(1)), bytes(map(len, ["ab", "c"])), list(log)]
    for kind in (bytes, bytearray):
        out += [error(kind, Refused()), error(kind, Raising(TypeError("t"))), error(kind, Raising(KeyError("k"))),
                error(kind, Items([1, 256])), error(kind, Items([1, "a"])), error(kind, Items([-1]))]
    return out

expected = [b"hi", bytearray(b"\x01\x02"), ["iter", "len", "iter"], b"ab", bytearray(b"a"), b"\x02\x01", [0, 1, 0]]
for kind, name, byte in (("bytes", "bytes", "bytes"), ("bytearray", "bytearray", "byte")):
    expected += [("TypeError", f"cannot convert 'Refused' object to {name}"),
                 ("TypeError", f"cannot convert 'Raising' object to {name}"), ("KeyError", "'k'"),
                 ("ValueError", f"{byte} must be in range(0, 256)"),
                 ("TypeError", "'str' object cannot be interpreted as an integer"),
                 ("ValueError", f"{byte} must be in range(0, 256)")]
assert_eq(made(), expected)

def nested():
    return made()

assert_eq(nested(), expected)
