# spec: PLS-315 17.5, 17.4.3
# description: an import statement at module level outside try reads
# __lazy_modules__ from globals that are a dict subclass's instance by
# its Python __getitem__ before each module it imports, a from-import and
# a future statement once; a KeyError means none, a module listed is
# imported lazily, and any other exception propagates. Imports in a
# class body, a function or a try, and lazy imports, read nothing.
# Inside functions and generators as at module level.
from harness import *
log = []
class Globals(dict):
    def __getitem__(self, key):
        for _ in (): pass
        log.append(key)
        if key == "__lazy_modules__":
            mode = dict.get(self, "mode")
            if mode == "list": return ["nowhere_a", "nowhere_b", "nowhere_pkg"]
            if mode == "first": return ["nowhere_a"]
            if mode == "value": raise ValueError("listing")
            if mode == "lookup": raise LookupError("listing")
        return dict.__getitem__(self, key)
def run(source, mode=None):
    g = Globals(mode=mode)
    del log[:]
    try:
        exec(source, g)
        result = sorted(k for k in dict.keys(g) if k not in ("__builtins__", "mode"))
    except Exception as error:
        result = (type(error).__name__, str(error))
    return result, list(log)
def cases():
    return [run("import nowhere_a, nowhere_b as b", "list"), run("from nowhere_pkg import x, y", "list"),
            run("import nowhere_a, nowhere_b", "first"), run("import nowhere_c"),
            run("if 1:\n    import nowhere_a", "list"), run("for _ in (1,):\n    import nowhere_a", "list"),
            run("try:\n    import nowhere_a\nexcept ImportError: pass", "list"),
            run("class C:\n    try: import nowhere_a\n    except ImportError: pass", "list"),
            run("def f():\n    import nowhere_a\ntry: f()\nexcept ImportError: pass", "list"),
            run("lazy import nowhere_a", "list"), run("from __future__ import annotations")[1],
            run("import nowhere_a", "value"), run("import nowhere_a", "lookup")]
def gen():
    yield cases()
expected = [(['b', 'nowhere_a'], ['__lazy_modules__', '__lazy_modules__']),
            (['x', 'y'], ['__lazy_modules__']),
            (('ModuleNotFoundError', "No module named 'nowhere_b'"), ['__lazy_modules__', '__lazy_modules__']),
            (('ModuleNotFoundError', "No module named 'nowhere_c'"), ['__lazy_modules__']),
            (['nowhere_a'], ['__lazy_modules__']),
            (['_', 'nowhere_a'], ['__lazy_modules__']),
            ([], ['ImportError']),
            (['C'], []),
            (['f'], ['f', 'ImportError']),
            (['nowhere_a'], []),
            ['__lazy_modules__'],
            (('ValueError', 'listing'), ['__lazy_modules__']),
            (('LookupError', 'listing'), ['__lazy_modules__'])]
assert_eq(cases(), expected)
assert_eq(next(gen()), expected)
def outer():
    return cases()
assert_eq(outer(), expected)
