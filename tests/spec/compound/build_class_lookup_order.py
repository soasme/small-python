# spec: PLS-315 16.4.1
# description: A class statement looks __build_class__ up in its builtins
# after its decorators and before its bases and keywords, inside a generic
# class's type parameters too; a builtins namespace's Python __missing__ or
# __getitem__, which may loop, answers it once, and its absence raises
# NameError before any base is evaluated.
from harness import *

log = []
builder = __build_class__
class Base: pass
class Missing(dict):
    def __missing__(self, key):
        for _ in (): pass
        log.append(key)
        if key == "__build_class__" and not self.get("lacking"): return builder
        if key in ("base", "deco", "kw"): return {"base": lambda: Base, "deco": lambda: (lambda c: c), "kw": lambda: {}}[key]
        if key == "__import__": return __import__
        raise KeyError(key)
class Mapping:
    def __getitem__(self, key):
        for _ in (): pass
        log.append(key)
        if key == "__build_class__": return builder
        if key == "base": return lambda: Base
        raise KeyError(key)
def run(src, builtins):
    del log[:]
    try:
        exec(src, {"__builtins__": builtins, "__name__": "m"})
        ended = []
    except NameError as e:
        ended = [str(e)]
    return [k for k in log if k in ("__build_class__", "base", "deco", "kw")] + ended
assert_eq(run("@deco()\nclass C(base(), **kw()): pass", Missing()), ["deco", "__build_class__", "base", "kw"])
assert_eq(run("@deco()\nclass H[T](base(), **kw()):\n    x = 1", Missing()), ["deco", "__build_class__", "base", "kw"])
assert_eq(run("def f():\n    @deco()\n    class I(base()):\n        for i in (): pass\n    return I\nf()", Missing()),
          ["deco", "__build_class__", "base"])
assert_eq(run("class C(base()): pass", Mapping()), ["__build_class__", "base"])
assert_eq(run("class C(base()): pass", Missing(lacking=True)), ["__build_class__", "__build_class__ not found"])
assert_eq(run("class C(base()): pass", {"base": lambda: Base}), ["__build_class__ not found"])
