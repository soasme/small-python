# spec: PLS-315 7.7.6, 7.7.7, 25.1.1, 24.1.1
# description: A list made from an iterable, and bytes(), ask its length hint after __iter__: __len__, else __length_hint__; their failures and unusable results raise, a TypeError falls back.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class Sized:
    def __init__(self, items=(1, 2)): self.items = items
    def __iter__(self):
        spin(); log.append("iter")
        return iter(self.items)
    def __len__(self):
        spin(); log.append("len")
        return len(self.items)
class Hinted:
    def __init__(self, items=(1, 2)): self.items = items
    def __iter__(self):
        spin(); log.append("iter")
        return iter(self.items)
    def __length_hint__(self):
        spin(); log.append("hint")
        return 2
class Plain:
    # Bodies with no call or loop.
    def __iter__(self): log.append("iter"); return iter((1, 2))
    def __len__(self): log.append("len"); return 2
class Generated:
    # An __iter__ that is a generator function: its body runs at the
    # first item, after the hint.
    def __iter__(self):
        log.append("iter")
        yield 1
    def __len__(self): log.append("len"); return 1
class Indexed:
    # The sequence protocol.
    def __getitem__(self, i):
        if i > 1: raise IndexError(i)
        return i
    def __len__(self): spin(); log.append("len"); return 2

def extend(x): l = [0]; l.extend(x); return l
def iadd(x): l = [0]; l += x; return l
def star(x): return [*x]
def star_tuple(x): return (*x,)
def bytes_of(x): return bytes(x)
def bytearray_extend(x): b = bytearray(); b.extend(x); return b
def init(x): l = [9]; l.__init__(x); return l
def listed(x): return list(x)
MAKERS = [listed, sorted, extend, iadd, star, star_tuple, bytes_of, bytearray_extend, init]

# __iter__ first, then the hint, for each way of making a list or bytes.
for make in MAKERS:
    for cls, asked in ((Sized, "len"), (Hinted, "hint"), (Plain, "len")):
        log.clear()
        make(cls())
        assert_eq(log, ["iter", asked], make.__name__ + " " + cls.__name__)
    log.clear()
    make(Generated())
    assert_eq(log, ["len", "iter"], make.__name__ + " Generated")
    log.clear()
    make(Indexed())
    assert_eq(log, ["len"], make.__name__ + " Indexed")
assert_eq(list(Sized((3, 4))), [3, 4])
assert_eq(star_tuple(Hinted((5,))), (5,))
assert_eq(bytes(Sized((1, 2))), b"\x01\x02")

# dir() lists what __dir__ returns as list() does.
class Directed:
    def __dir__(self): return Sized(("b", "a"))
log.clear()
assert_eq(dir(Directed()), ["a", "b"])
assert_eq(log, ["iter", "len"])

# A list subclass's own __len__ is asked too.
class Listed(list):
    def __iter__(self): log.append("iter"); return iter((7,))
    def __len__(self): log.append("len"); return 1
log.clear()
assert_eq(list(Listed()), [7])
assert_eq(log, ["iter", "len"])

# Other consumers ask no hint.
for consume in (tuple, set, frozenset, sum, max, any, bytearray, dict.fromkeys, lambda x: {*x},
                lambda x: print(*x, end=""), lambda x: ''.join(map(str, x)), lambda x: 3 in x):
    log.clear()
    consume(Sized())
    assert_eq(log, ["iter"])
log.clear()
a, b = Sized()
assert_eq(log, ["iter"])

# A __len__ raising TypeError, or returning a non-integer, is no length:
# __length_hint__ is asked next, and its TypeError means no hint either.
def raising(error):
    def method(self):
        spin()
        raise error
    return method
def returning(value):
    def method(self):
        spin()
        return value
    return method
def make(**methods):
    methods["__iter__"] = Sized.__iter__
    methods["items"] = (1, 2)
    return type("X", (), methods)()
for hint in (returning(NotImplemented), raising(TypeError("t")), returning(True), returning(0), returning(9)):
    for length in (raising(TypeError("t")), returning("a"), None):
        methods = {"__length_hint__": hint, **({"__len__": length} if length else {})}
        for make_list in MAKERS:
            assert_eq(list(make_list(make(**methods)))[-2:], [1, 2], make_list.__name__)

# Every other failure propagates, after __iter__.
cases = [
    ({"__len__": raising(ValueError("v"))}, ValueError, "v"),
    ({"__len__": returning(-1)}, ValueError, "__len__() should return >= 0"),
    ({"__len__": returning(2 ** 70)}, OverflowError, "cannot fit 'int' into an index-sized integer"),
    ({"__len__": raising(TypeError("t")), "__length_hint__": raising(ValueError("v"))}, ValueError, "v"),
    ({"__length_hint__": raising(KeyError("k"))}, KeyError, "'k'"),
    ({"__length_hint__": returning("a")}, TypeError, "X.__length_hint__() must return an int, not str"),
    ({"__length_hint__": returning(-1)}, ValueError, "X.__length_hint__() must return a non-negative int"),
    ({"__length_hint__": returning(2 ** 70)}, OverflowError, "Python int too large to convert to C ssize_t"),
    ({"__length_hint__": returning(-2 ** 70)}, OverflowError, "Python int too large to convert to C ssize_t"),
]
for methods, error, message in cases:
    for make_list in MAKERS:
        log.clear()
        assert_raises(error, make_list, make(**methods), message=message)
        assert_eq(log, ["iter"], make_list.__name__)

# The hint is the iterable's, not its iterator's.
class Iterator:
    def __iter__(self): return self
    def __next__(self): raise StopIteration
    def __len__(self): raise ValueError("iterator")
class Source:
    def __iter__(self): spin(); return Iterator()
assert_eq(list(Source()), [])

# In a generator, the calls are the generator's.
def gen():
    yield list(Sized((8,)))
    yield [*Hinted((9,))]
log.clear()
assert_eq(list(gen()), [[8], [9]])
assert_eq(log, ["iter", "len", "iter", "hint"])
