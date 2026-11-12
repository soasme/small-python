# spec: PLS-315 7.7.8, 23.1.5, 24.3, 26.1.1
# description: str.join, bytes.join and dict()'s pairs take their argument's iterator once and list its items as list() lists that iterator: its own __iter__ again, then its length hint.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class Fresh:
    # An __iter__ returning a built-in iterator, whose own steps are silent.
    def __init__(self, items): self.items = items
    def __iter__(self):
        spin(); log.append("iter")
        return iter(self.items)
    def __len__(self):
        log.append("len")
        return 2
class Own:
    # An iterator that is its own iterable, and sized.
    def __init__(self, items): self.items = list(items)
    def __iter__(self):
        spin(); log.append("iter")
        return self
    def __next__(self):
        if not self.items: raise StopIteration
        return self.items.pop(0)
    def __len__(self):
        spin(); log.append("len")
        return len(self.items)
class Plain(Own):
    # Bodies with no call or loop.
    def __iter__(self): log.append("iter"); return self
    def __len__(self): log.append("len"); return 2

JOINS = [("str.join", lambda x: "-".join(x), "ab", "a-b"),
         ("bytes.join", lambda x: b"-".join(x), (b"a", b"b"), b"a-b"),
         ("bytearray.join", lambda x: bytearray(b"-").join(x), (b"a", b"b"), bytearray(b"a-b")),
         ("dict pair", lambda x: dict([x]), "ab", {"a": "b"})]
for name, join, items, result in JOINS:
    log.clear()
    assert_eq(join(Fresh(items)), result, name)
    assert_eq(log, ["iter"], name)
    for cls in (Own, Plain):
        log.clear()
        assert_eq(join(cls(items)), result, name)
        assert_eq(log, ["iter", "iter", "len"], name + " " + cls.__name__)

# The list is complete before any item is checked.
def failing():
    yield 1
    raise ValueError("late")
assert_raises(ValueError, "".join, failing(), message="late")
class Late(Own):
    def __next__(self):
        if not self.items: raise ValueError("late")
        return self.items.pop(0)
assert_raises(ValueError, "".join, Late([1]), message="late")
assert_raises(TypeError, "".join, Own(["a", 1]), message="sequence item 1: expected str instance, int found")

# A non-iterable argument is refused with the caller's message; an iterator
# that is not itself iterable fails in the listing, as list() would.
assert_raises(TypeError, "".join, 5, message="can only join an iterable")
assert_raises(TypeError, b"".join, 5, message="can only join an iterable")
class Bare:
    def __next__(self): raise StopIteration
class Handing:
    def __iter__(self): spin(); return Bare()
assert_raises(TypeError, "".join, Handing(), message="'Bare' object is not iterable")
assert_raises(TypeError, b"".join, Handing(), message="'Bare' object is not iterable")
with Raises(TypeError, "'Bare' object is not iterable"):
    dict([Handing()])

# The iterator's length hint errors propagate.
class Unsized(Own):
    def __len__(self): spin(); raise ValueError("size")
for name, join, items, result in JOINS:
    assert_raises(ValueError, join, Unsized(items), message="size")
