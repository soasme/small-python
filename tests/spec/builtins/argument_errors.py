# spec: PLS-315 7.4.4, 21.3.2, 22.1.5, 28.7
# description: argument errors of built-ins with keyword-only parameters, slot wrappers and special methods that are methods.
from harness import *

def message(call, *args, **kwargs):
    return str(assert_raises(TypeError, call, *args, **kwargs))

# Keyword-only parameters are counted before they are named.
assert_eq(message([].sort, a=1, b=2, c=3), "sort() takes at most 2 keyword arguments (3 given)")
assert_eq(message(min, [1], a=1, b=2, c=3), "min() takes at most 2 keyword arguments (3 given)")
assert_eq(message(NameError, name="n", obj=1), "NameError() takes at most 1 keyword argument (2 given)")
class Missing(AttributeError):
    pass
assert_eq(message(Missing, a=1, b=2, c=3), "AttributeError() takes at most 2 keyword arguments (3 given)")
assert_eq(message(int.from_bytes, b"\x01", "big", False), "from_bytes() takes at most 2 positional arguments (3 given)")
assert_eq(int.from_bytes(b"\xff", "big", signed=True), -1)

# Slot wrappers take their operands by position only.
assert_eq(message((1).__add__), "expected 1 argument, got 0")
assert_eq(message(int.__add__, 1, 2, 3), "expected 1 argument, got 2")
assert_eq(message((1).__add__, other=2), "wrapper __add__() takes no keyword arguments")
assert_eq(message(list.__len__, [], x=1), "wrapper __len__() takes no keyword arguments")
assert_eq(message([0].__setitem__, 0), "__setitem__ expected 2 arguments, got 1")
assert_eq(message(memoryview(b"a").__buffer__), "__buffer__ expected 1 argument, got 0")
assert_eq(message(memoryview(b"a").__len__, 1), "expected 0 arguments, got 1")
assert_eq(message(type.__or__, int), "expected 1 argument, got 0")
assert_eq(message((1).__hash__, 2), "expected 0 arguments, got 1")
assert_eq(message((1).__hash__, x=1), "wrapper __hash__() takes no keyword arguments")
assert_eq(message(int.__hash__), "descriptor '__hash__' of 'int' object needs an argument")
assert_eq(message(frozenset.__hash__, 1), "descriptor '__hash__' requires a 'frozenset' object but received a 'int'")

# These special methods are method descriptors.
assert_eq(message({}.__contains__), "dict.__contains__() takes exactly one argument (0 given)")
assert_eq(message(frozenset().__contains__, x=1), "frozenset.__contains__() takes no keyword arguments")
assert_eq(message([].__getitem__, 1, 2), "list.__getitem__() takes exactly one argument (2 given)")
assert_eq(message((1).__round__, 1, 2), "__round__ expected at most 1 argument, got 2")
assert_eq(message((1.5).__round__, ndigits=1), "float.__round__() takes no keyword arguments")
assert_eq(message(int.__round__), "unbound method int.__round__() needs an argument")
assert_eq(message(float.__round__, 1), "descriptor '__round__' for 'float' objects doesn't apply to a 'int' object")
assert_eq(message(memoryview(b"a").tolist, 1), "memoryview.tolist() takes no arguments (1 given)")
assert_eq(bytearray(b"ab").hex(":", -2**63), "6162")
