# spec: PLS-315 20.1.4
# description: object.__reduce__, __reduce_ex__ and __getstate__ name the intrinsic reconstruction functions.
from harness import *

class Plain:
    def __init__(self):
        self.x = 1

class Number(int):
    pass

class Slotted:
    __slots__ = ("a", "__b")
    def __init__(self):
        self.a = 2

class Keyword:
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)
    def __getnewargs_ex__(self):
        return (1,), {"k": 2}

# Protocol 2 and later: %NewObj% or %NewObjEx% with the class and arguments.
newobj, args, state, listitems, dictitems = Plain().__reduce_ex__(2)
assert_eq((newobj.__name__, args, state, listitems, dictitems), ("__newobj__", (Plain,), {"x": 1}, None, None))
assert_type(newobj(*args), Plain)
assert_ne(newobj.__module__, "builtins")
newobj_ex, args, state, _, _ = Keyword().__reduce_ex__(4)
assert_eq((newobj_ex.__name__, args, state), ("__newobj_ex__", (Keyword, (1,), {"k": 2}), None))
assert_type(newobj_ex(*args), Keyword)
# Slots go in a second state dict, mangled; the names are cached as __slotnames__.
_, _, state, _, _ = Slotted().__reduce_ex__(2)
assert_eq(state, (None, {"a": 2}))
assert_eq(Slotted.__slotnames__, ["a", "_Slotted__b"])
# Lists and dicts carry iterators over their items.
class L(list): pass
_, _, _, items, _ = L([1, 2]).__reduce_ex__(2)
assert_eq(list(items), [1, 2])
class D(dict): pass
_, _, _, _, items = D(a=1).__reduce_ex__(2)
assert_eq(list(items), [("a", 1)])

# Protocols 0 and 1: %Reconstructor% with the first built-in base.
reconstructor, args, state = Plain().__reduce_ex__(1)
assert_eq((reconstructor.__name__, args, state), ("_reconstructor", (Plain, object, None), {"x": 1}))
assert_type(reconstructor(*args), Plain)
reconstructor, args = Number(5).__reduce_ex__(0)
assert_eq(args, (Number, int, 5))
rebuilt = reconstructor(*args)
assert_eq((type(rebuilt), rebuilt), (Number, 5))
assert_eq(object().__reduce__()[0].__name__, "_reconstructor")
e = assert_raises(TypeError, Slotted().__reduce_ex__, 1)
assert_eq(str(e), "a class that defines __slots__ without defining __getstate__ cannot be pickled")

# __reduce_ex__ defers to an overridden __reduce__.
class Custom:
    def __reduce__(self):
        return "custom"
assert_eq(Custom().__reduce_ex__(2), "custom")
assert_eq(str(assert_raises(TypeError, object().__reduce_ex__, "2")), "'str' object cannot be interpreted as an integer")

# The default __getstate__.
assert_eq(Plain().__getstate__(), {"x": 1})
assert_eq(object().__getstate__(), None)
assert_eq(Slotted().__getstate__(), (None, {"a": 2}))

# __getnewargs__ results are checked.
class BadArgs:
    def __getnewargs__(self):
        return [1]
e = assert_raises(TypeError, BadArgs().__reduce_ex__, 2)
assert_eq(str(e), "__getnewargs__ should return a tuple, not 'list'")
class BadArgsEx:
    def __getnewargs_ex__(self):
        return ((), {}, 1)
e = assert_raises(ValueError, BadArgsEx().__reduce_ex__, 2)
assert_eq(str(e), "__getnewargs_ex__ should return a tuple of length 2, not 3")
