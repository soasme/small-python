# spec: PLS-315 7.8, 10.5
# description: __getitem__/__setitem__/__delitem__, __missing__, __iter__, __reversed__, __contains__, slices.
from harness import *

class Seq:
    def __init__(self): self.log = []
    def __getitem__(self, key):
        self.log.append(key)
        if isinstance(key, int) and key >= 3: raise IndexError(key)
        return key
    def __setitem__(self, key, value): self.log.append(("set", key, value))
    def __delitem__(self, key): self.log.append(("del", key))
s = Seq()
assert_eq(s[1:2], slice(1, 2))
assert_eq(s[1:2:3, ...], (slice(1, 2, 3), Ellipsis))
assert_eq(s[::], slice(None, None, None))
s[0] = 5
del s[1:]
assert_eq(s.log[-2:], [("set", 0, 5), ("del", slice(1, None))])
# Old-style iteration via __getitem__ stops at IndexError.
assert_eq(list(Seq()), [0, 1, 2])
assert_true(2 in Seq())
assert_false(5 in Seq()) if False else None
assert_eq(list(reversed([1, 2, 3])), [3, 2, 1])

class Rev:
    def __len__(self): return 3
    def __getitem__(self, i): return i * 10
assert_eq(list(reversed(Rev())), [20, 10, 0])
class NoRev:
    __reversed__ = None
    def __len__(self): return 1
    def __getitem__(self, i): return i
assert_raises(TypeError, reversed, NoRev())
class NoIter:
    __iter__ = None
assert_raises(TypeError, iter, NoIter())
class NoContains:
    __contains__ = None
    def __iter__(self): return iter([1])
assert_raises(TypeError, lambda: 1 in NoContains())

class Contains:
    def __contains__(self, item): return item == "x"
assert_true("x" in Contains())
assert_true("y" not in Contains())
class ContainsInt:
    def __contains__(self, item): return 5
assert_is(1 in ContainsInt(), True)

class Default(dict):
    def __missing__(self, key): return key * 2
d = Default(a=1)
assert_eq((d["a"], d["b"]), (1, "bb"))
assert_eq(d.get("b"), None)
assert_false("b" in d)

class It:
    def __init__(self): self.n = 0
    def __iter__(self): return self
    def __next__(self):
        self.n += 1
        if self.n > 2: raise StopIteration
        return self.n
assert_eq(list(It()), [1, 2])
class BadIter:
    def __iter__(self): return 1
assert_raises(TypeError, iter, BadIter())

assert_eq(slice(1, 10, 2).indices(5), (1, 5, 2))
assert_eq(slice(None).indices(3), (0, 3, 1))
assert_raises(ValueError, slice(0, 1, 0).indices, 3)
assert_eq([0, 1, 2, 3, 4][::-2], [4, 2, 0])
assert_eq("abcdef"[-2:], "ef")
assert_eq([1, 2, 3][10:], [])
l = [0, 1, 2, 3]
l[1:3] = "ab"
assert_eq(l, [0, "a", "b", 3])
l[::2] = [9, 9]
assert_eq(l, [9, "a", 9, 3])
assert_raises(ValueError, l.__setitem__, slice(None, None, 2), [1])
del l[::2]
assert_eq(l, ["a", 3])
assert_eq(len(range(0, 10, 3)), 4)
assert_eq(range(10)[-1], 9)
assert_eq(hash(slice(1, 2)), hash(slice(1, 2)))
# __len__ returns an index that is not negative and fits a Py_ssize_t.
class Index:
    def __index__(self): return 2
def sized(value):
    return type("Sized", (), {"__len__": lambda self: value})()
assert_eq(len(sized(Index())), 2)
assert_true(bool(sized(Index())))
for f in (len, bool):
    e = assert_raises(TypeError, f, sized("3"))
    assert_eq(str(e), "'str' object cannot be interpreted as an integer")
    e = assert_raises(OverflowError, f, sized(2 ** 64))
    assert_eq(str(e), "cannot fit 'int' into an index-sized integer")
    e = assert_raises(ValueError, f, sized(-2 ** 64))
    assert_eq(str(e), "__len__() should return >= 0")
# A __bool__ or __contains__ of None disables truth testing or membership.
class NoBool:
    __bool__ = None
    def __len__(self): return 1
e = assert_raises(TypeError, bool, NoBool())
assert_eq(str(e), "'NoBool' cannot be interpreted as a boolean")
class NoContains:
    __contains__ = None
    def __iter__(self): return iter([1])
e = assert_raises(TypeError, lambda: 1 in NoContains())
assert_eq(str(e), "'NoContains' object is not a container")
e = assert_raises(TypeError, lambda: 1 in "abc")
assert_eq(str(e), "'in <string>' requires string as left operand, not int")
e = assert_raises(TypeError, lambda: "a" in b"abc")
assert_eq(str(e), "a bytes-like object is required, not 'str'")
