# spec: PLS-315 16.4.2, 16.6.1
# description: a class body stores __module__, __qualname__ and
# __firstlineno__, then its statements' names, then __annotate_func__ when
# it has annotations, conditional ones included, then
# __static_attributes__ and __classdictcell__; the body cannot read its
# own __annotate_func__. A module body executed with a mapping binds
# __annotate__, then __conditional_annotations__, before its first
# statement, every module annotation counting as conditional: one that
# raises before a later annotation leaves only the first in __annotate__,
# and an attribute's annotation alone binds the set.
from harness import *

log = []

class Namespace(dict):
    def __setitem__(self, key, value):
        log.append(key)
        super().__setitem__(key, value)

class Meta(type):
    @classmethod
    def __prepare__(mcls, name, bases): return Namespace()

class Annotated(metaclass=Meta):
    a = 1
    if a:
        x: int = 2
    y: str
    try: __annotate_func__
    except NameError: missing = True
    b = 3

assert_eq(log, ["__module__", "__qualname__", "__firstlineno__", "a", "x", "missing", "b",
                "__annotate_func__", "__static_attributes__", "__classdictcell__"])
assert_eq(Annotated.__annotations__, {"x": int, "y": str})
log.clear()

class Plain(metaclass=Meta):
    a = 1
    def f(self): self.z = 1

assert_eq(log, ["__module__", "__qualname__", "__firstlineno__", "a", "f", "__static_attributes__", "__classdictcell__"])
log.clear()

exec("a = 1\nx: int = 2\nif a:\n    y: str = 3\nb = 3\n", {}, Namespace())
assert_eq(log, ["__annotate__", "__conditional_annotations__", "a", "x", "y", "b"])
log.clear()
exec("a = 1\nx: int = 2\n", {}, Namespace())
assert_eq(log, ["__annotate__", "__conditional_annotations__", "a", "x"])
log.clear()

ns = {}
try: exec("x: int = 1\nraise KeyError\ny: str = 2\n", ns)
except KeyError: pass
assert_eq((ns["__annotate__"](1), ns["__conditional_annotations__"]), ({"x": int}, {0}))
ns = {}
exec("class A: pass\nA.q: int = 1\n", ns)
assert_eq((ns["__conditional_annotations__"], "__annotate__" in ns), (set(), False))
