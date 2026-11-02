# spec: PLS-315 19.2, 20.3.1, 20.8, 25.3, 25.4, 27.1.4
# description: T.__new__ of built-in classes: mutable classes start empty, others build from their arguments.
from harness import *

# list, dict, set and bytearray ignore the arguments; __init__ fills.
assert_eq(list.__new__(list, [1], 2, x=3), [])
assert_eq(dict.__new__(dict, {1: 2}, x=3), {})
assert_eq(set.__new__(set, [1], 2, x=3), set())
assert_eq(bytearray.__new__(bytearray, 1, 2, 3, 4, x=5), bytearray())
items = list.__new__(list)
list.__init__(items, "ab")
assert_eq(items, ["a", "b"])
class Items(list): pass
assert_type(list.__new__(Items, [1]), Items)
assert_eq(list.__new__(Items, [1]), [])

# Immutable classes build from the arguments.
assert_eq(tuple.__new__(tuple, "ab"), ("a", "b"))
assert_eq(str(assert_raises(TypeError, tuple.__new__, tuple, 1, 2)), "tuple expected at most 1 argument, got 2")
assert_eq(str(assert_raises(TypeError, int.__new__, int, 1, 2, 3)), "int() takes at most 2 arguments (3 given)")
assert_eq(str(assert_raises(TypeError, int, 1, 2, 3)), "int expected at most 2 arguments, got 3")
assert_eq(str(assert_raises(TypeError, str.__new__, str, 1, 2, 3, 4)), "str() takes at most 3 arguments (4 given)")
assert_eq(str(assert_raises(TypeError, str, 1, 2, 3, 4)), "str expected at most 3 arguments, got 4")
class Small(int): pass
class Text(str): pass
assert_eq(str(assert_raises(TypeError, Small, 1, 2, 3)), "int() takes at most 2 arguments (3 given)")
assert_eq(str(assert_raises(TypeError, Text, 1, 2, 3, 4)), "str() takes at most 3 arguments (4 given)")

# range, slice and sentinel define their own __new__.
for kind in (range, slice, sentinel):
    assert_true("__new__" in kind.__dict__)
assert_eq(range.__new__(range, 3), range(3))
assert_eq(slice.__new__(slice, 1, 2), slice(1, 2))
assert_eq(str(assert_raises(TypeError, range.__new__, range)), "range expected at least 1 argument, got 0")
assert_eq(str(assert_raises(TypeError, slice.__new__, slice)), "slice expected at least 1 argument, got 0")
marker = sentinel.__new__(sentinel, "MARKER")
assert_eq((repr(marker), type(marker)), ("MARKER", sentinel))
e = assert_raises(TypeError, range.__new__, int, 1)
assert_eq(str(e), "range.__new__(int): int is not a subtype of range")

# enumerate.__new__ checks its arguments as a function with keywords does.
assert_eq(list(enumerate.__new__(enumerate, "a", start=2)), [(2, "a")])
e = assert_raises(TypeError, enumerate.__new__, enumerate)
assert_eq(str(e), "enumerate() missing required argument 'iterable' (pos 1)")
class Numbered(enumerate): pass
assert_eq(str(assert_raises(TypeError, Numbered)), "enumerate() missing required argument 'iterable' (pos 1)")
assert_eq(str(assert_raises(TypeError, Numbered, [], 1, 2)), "enumerate() takes at most 2 arguments (3 given)")
assert_eq(str(assert_raises(TypeError, enumerate)), "enumerate() missing required argument 'iterable'")

assert_eq(str(assert_raises(TypeError, super, 1, 2, 3)), "super() expected at most 2 arguments, got 3")
