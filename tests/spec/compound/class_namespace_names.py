# spec: PLS-315 16.4.2, 16.6.1
# description: a class body binds its implicit names through the Python
# __setitem__ of the namespace __prepare__ returned, which may loop, and
# reads __name__ through its Python __getitem__, falling back to the
# globals on a KeyError: __module__, __qualname__, __firstlineno__, under
# PEP 563 __annotations__, then __doc__ before the statements, and
# __annotate_func__, __static_attributes__, __classdictcell__ and
# __classcell__ after them; __annotations__ only when the namespace's
# __getitem__ raises KeyError for it. An error from any of those calls
# propagates and makes no class. Under PEP 563 an attribute's annotation alone sets
# up __annotations__, and no def or annotation needs __classdictcell__.
# Inside functions as at module level. A generic class's namespace whose
# keys include one that is not a str reads __name__ from the globals too.
from harness import *

log = []

class Namespace(dict):
    def __setitem__(self, key, value):
        for _ in (): pass
        log.append(key)
        if key == self.get("fail"): raise LookupError(key)
        super().__setitem__(key, value)
    def __getitem__(self, key):
        for _ in (): pass
        log.append(("get", key))
        if key == "__name__" and "mapped" in self: return "mapped"
        return super().__getitem__(key)

class Meta(type):
    @classmethod
    def __prepare__(mcls, name, bases, **kw):
        ns = Namespace()
        for k, v in kw.items(): dict.__setitem__(ns, k, v)
        return ns
    def __new__(mcls, name, bases, ns, **kw):
        return super().__new__(mcls, name, bases, dict(ns))

def define():
    class Plain(metaclass=Meta):
        """doc"""
        x: int = 1
        def f(self):
            self.a = __class__
    return Plain

before = [("get", "__name__"), "__module__", "__qualname__", "__firstlineno__", "__doc__"]
after = ["__annotate_func__", "__static_attributes__", "__classdictcell__", "__classcell__"]
P = define()
assert_eq(log, before + ["x", "f"] + after)
assert_eq((P.__module__, P.__qualname__, P.__doc__, P.__static_attributes__), (__name__, "define.<locals>.Plain", "doc", ("a",)))
log.clear()

class Named(metaclass=Meta, mapped=1):
    pass

assert_eq((log, Named.__module__), ([("get", "__name__"), "__module__", "__qualname__", "__firstlineno__", "__static_attributes__"], "mapped"))

def failing(key):
    log.clear()
    try:
        class Fails(metaclass=Meta, fail=key):
            def f(self): return __class__
    except LookupError as e:
        return e.args, log[-1]

assert_eq([failing(k) for k in ("__module__", "__qualname__", "__static_attributes__", "__classcell__")],
          [(("__module__",), "__module__"), (("__qualname__",), "__qualname__"),
           (("__static_attributes__",), "__static_attributes__"), (("__classcell__",), "__classcell__")])

log.clear()
ns = {"Meta": Meta}
exec("from __future__ import annotations\n"
     "class Lazy(metaclass=Meta):\n    '''doc'''\n    x: int = 2\n    def f(self): pass\n"
     "class Attr(metaclass=Meta):\n    Meta.y: int\n", ns)
lookup = ("get", "__annotations__")
assert_eq(log, before[:4] + [lookup, "__annotations__", "__doc__", "x", lookup, "f", "__static_attributes__"] +
          before[:4] + [lookup, "__annotations__", ("get", "Meta"), "__static_attributes__"])
log.clear()

# An __annotations__ the namespace has is kept.
class Kept(dict):
    def __getitem__(self, key):
        for _ in (): pass
        log.append(("get", key))
        if key == "__annotations__": return {"kept": 1}
        return super().__getitem__(key)
class KeptMeta(type):
    @classmethod
    def __prepare__(mcls, name, bases): return Kept()
ns = {"KeptMeta": KeptMeta}
exec("from __future__ import annotations\nclass K(metaclass=KeptMeta):\n    x: int\n", ns)
assert_eq((log, "__annotations__" in ns["K"].__dict__), ([("get", "__name__"), lookup, lookup], False))

# A module's or a plain namespace's __annotations__ is kept as well.
ns = {"__annotations__": {"a": 1}}
exec("from __future__ import annotations\nx: int\n", ns)
class Preset(type):
    @classmethod
    def __prepare__(mcls, name, bases): return {"__annotations__": {"b": 2}}
exec("from __future__ import annotations\nclass P(metaclass=Preset):\n    y: int\n", ns2 := {"Preset": Preset})
assert_eq((ns["__annotations__"], ns2["P"].__annotations__), ({"a": 1, "x": "int"}, {"b": 2, "y": "int"}))

# A generic class's namespace with a __missing__ and a key that is not a
# str: __name__ is not found among its keys and is read from the globals.
class Missing(dict):
    def __missing__(self, key):
        raise KeyError(key)
class Keyed(type):
    @classmethod
    def __prepare__(mcls, name, bases): return Missing({1: 2})
    def __new__(mcls, name, bases, ns): return super().__new__(mcls, name, bases, dict(ns))
class G[T](metaclass=Keyed): pass
assert_eq((G.__module__, G.__dict__[1]), (__name__, 2))
