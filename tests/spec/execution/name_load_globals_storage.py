# spec: PLS-315 9.3.1, 9.3.2
# description: a module or class body's name lookup past its locals reads
# exec()'s globals, a dict subclass, by their dictionary storage, never
# their __getitem__ (LoadFromLocals); a function's global lookup, a name
# a body declares global, and an annotation scope's global name call it
# (LoadGlobal). A KeyError from the locals' __getitem__ leaves the name to
# the globals' storage, even when __getitem__ refuses a key it has.
from harness import *

log = []
class Globals(dict):
    def __getitem__(self, key):
        log.append(key)
        if key == "hidden": raise KeyError(key)
        return super().__getitem__(key)

# Module level: the locals are the globals, read once through __getitem__.
g = Globals(y=1, hidden=2)
exec("a = len\nb = y\nc = hidden\n", g)
assert_eq(log, ["len", "y", "hidden"])
assert_eq(dict.__getitem__(g, "c"), 2)

# A function reads its globals through __getitem__.
log.clear()
exec("def f(): return y, len\nd = f()\n", g)
assert_eq(log, ["f", "y", "len"])
assert_eq(dict.__getitem__(g, "d"), (1, len))

# A class body reads them by storage, a name it declares global through __getitem__.
log.clear()
exec("class C:\n    a = y\n    b = len\n    c = hidden\n"
     "class D:\n    global y\n    a = y\n", g)
assert_eq(log, ["y"])
assert_eq((g["C"].a, g["C"].b, g["C"].c, g["D"].a), (1, len, 2, 1))
assert_eq(g["C"].__module__, "builtins")

# exec()'s separate locals: the locals through __getitem__, the globals by storage.
class Locals(dict):
    def __getitem__(self, key):
        log.append(("locals", key))
        return super().__getitem__(key)
log.clear()
exec("a = y\nb = len\nc = hidden\n", g, loc := Locals())
assert_eq(log, [("locals", "y"), ("locals", "len"), ("locals", "hidden")])
assert_eq(dict(loc), {"a": 1, "b": len, "c": 2})

# A class body's own namespace (__prepare__) through __getitem__, then the globals by storage.
class Namespace(dict):
    def __getitem__(self, key):
        log.append(("ns", key))
        return super().__getitem__(key)
class Meta(type):
    @classmethod
    def __prepare__(mcls, name, bases): return Namespace()
g["Meta"] = Meta
log.clear()
exec("class E(metaclass=Meta):\n    a = y\n", g)
assert_eq(log, ["Meta", ("ns", "__name__"), ("ns", "y")])

# An annotation scope reads a global name of its class through __getitem__.
log.clear()
exec("class F:\n    x: y\nann = F.__annotate__(1)\n", g)
assert_eq(dict.__getitem__(g, "ann"), {"x": 1})
assert_eq(log, ["F", "y"])

# Missing everywhere: one __getitem__ call, then NameError.
log.clear()
e = assert_raises(NameError, exec, "q = nope", g)
assert_eq((str(e), log), ("name 'nope' is not defined", ["nope"]))
