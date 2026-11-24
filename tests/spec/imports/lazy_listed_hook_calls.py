# spec: PLS-315 17.4, 17.5
# description: At module level, with __lazy_modules__ in the globals, an
# import of a module it does not name, and a from-import of one, call the
# builtins' __import__, a Python function that may loop, as without it,
# and bind what it returns; a module it names is imported lazily, calling
# nothing; an exception from __import__ propagates, the names before it
# bound.
from harness import *

class Part: pass
top = Part(); top.b = Part(); top.b.c = "leaf"
calls = []
def hook(name, globals=None, locals=None, fromlist=(), level=0):
    for _ in range(2): pass
    calls.append((name, fromlist))
    if name == "broken": raise LookupError(name)
    return top

lazy = __import__("builtins").__lazy_import__
def run(source):
    names = {"__builtins__": {"__import__": hook, "__lazy_import__": lazy}, "__lazy_modules__": ["listed"]}
    del calls[:]
    try:
        exec(source, names)
        result = sorted(k for k in names if k not in ("__builtins__", "__lazy_modules__"))
    except Exception as e:
        result = (type(e).__name__, str(e)), sorted(k for k in names if k not in ("__builtins__", "__lazy_modules__"))
    return result, calls[:]
def cases():
    return [run("import top.b.c as x"), run("import one, two"), run("from top import b"), run("import listed, one"),
            run("from listed import z"), run("import one, broken, two")]
expected = [(["x"], [("top.b.c", None)]), (["one", "two"], [("one", None), ("two", None)]), (["b"], [("top", ("b",))]),
            (["listed", "one"], [("one", None)]), (["z"], []),
            ((("LookupError", "broken"), ["one"]), [("one", None), ("broken", None)])]
assert_eq(cases(), expected)
assert_eq(cases(), expected)
