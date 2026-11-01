# spec: PLS-315 17.4.3
# description: from ... import * reads __all__ or the public keys of __dict__ through attribute access, from any object.
from harness import *

Module = type(__import__("builtins"))

def star(obj, namespace=None):
    """Run "from x import *" where importing x gives obj; return the bound names."""
    scope = {"__builtins__": {"__import__": lambda *args: obj}}
    target = scope if namespace is None else namespace
    exec("from x import *", scope, target)
    return sorted(name for name in target if name != "__builtins__")

def fails(error, message, obj):
    assert_eq(str(assert_raises(error, star, obj)), message)

# Without __all__, the public keys of __dict__, of any object that has one.
def function(): pass
function.attr, function._hidden = 1, 2
assert_eq(star(function), ["attr"])
class Plain: pass
instance = Plain()
instance.a, instance._b = 1, 2
assert_eq(star(instance), ["a"])
fails(ImportError, "from-import-* object has no __dict__ and no __all__", 5)

# __all__ is indexed from 0 until IndexError, and found by attribute lookup.
class Letters:
    def __getitem__(self, i):
        if i < 2:
            return "ab"[i]
        raise IndexError
class Listed:
    __all__ = Letters()
    a, b, c = 1, 2, 3
assert_eq(star(Listed), ["a", "b"])
class Dynamic(Module):
    def __getattr__(self, name):
        if name == "__all__":
            return ["z"]
        if name == "z":
            return 26
        raise AttributeError(name)
assert_eq(star(Dynamic("dynamic")), ["z"])
class Text(str): pass
subclassed = Module("subclassed")
subclassed.__all__, subclassed.v = [Text("v")], 4
assert_eq(star(subclassed), ["v"])
class Upper(dict):
    def __setitem__(self, key, value):
        super().__setitem__(key.upper(), value)
mapped = Module("mapped")
mapped.k = 1
assert_eq(star(mapped, Upper()), ["K"])

# Names must be str; the message names the module through its __name__.
keyed = Module("keyed")
keyed.__dict__[1] = 2
fails(TypeError, "Key in keyed.__dict__ must be str, not int", keyed)
listed = Module("listed")
listed.__all__ = ["x", 1]
listed.x = 0
fails(TypeError, "Item in listed.__all__ must be str, not int", listed)
listed.__name__ = 5
fails(TypeError, "module __name__ must be a string, not int", listed)
del listed.__name__
assert_raises(AttributeError, star, listed)
missing = Module("missing")
missing.__all__ = ["absent"]
fails(AttributeError, "module 'missing' has no attribute 'absent'", missing)
class Broken:
    @property
    def __all__(self):
        raise KeyError("x")
assert_raises(KeyError, star, Broken())
