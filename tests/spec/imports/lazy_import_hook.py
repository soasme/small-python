# spec: PLS-315 17.5, 17.4.3
# description: a lazy import, or one __lazy_modules__ makes lazy, calls
# the frame's builtins' __lazy_import__ at the statement when it is not
# the original, with __import__'s five arguments, and binds its result as
# an eager import binds __import__'s: an as-name reads the dotted parts,
# a from-name the attribute. In globals with a Python __getitem__ the
# list is read before each module. Without __lazy_import__ the statement
# raises ImportError; the lazy-imports filter is asked only for the
# original function.
from harness import assert_eq
import builtins

log = []

class R:
    def __init__(self, n): self.n = n
    def __getattr__(self, a): return R(self.n + "." + a)
    def __repr__(self): return "R(" + self.n + ")"

def hook(*a, **k):
    for _ in (): pass
    log.append((a[0], type(a[1]).__name__, type(a[2]).__name__, a[3], a[4], k))
    return R(a[0])

def eager(*a):
    log.append(("eager", a[0], a[3]))
    return R("E:" + a[0])

class Listing(dict):
    def __getitem__(self, key):
        for _ in (): pass
        if key == "__lazy_modules__": log.append("read")
        return dict.__getitem__(self, key)

def run(source, globals_type=dict, **builtin):
    b = dict(vars(builtins)); b.update(builtin)
    for k, v in builtin.items():
        if v is None: del b[k]
    g = globals_type(__builtins__=b, __name__="m", __lazy_modules__=["json", "os"])
    del log[:]
    try:
        exec(source, g)
        result = g.get("r")
    except Exception as e:
        result = (type(e).__name__, str(e))
    return result, list(log)

source = "lazy import json\nlazy import os.path as p\nlazy import os.path\nlazy from json import dumps, loads as L\nr = (json, p, os, dumps, L)"
result, calls = run(source, __lazy_import__=hook)
assert_eq(repr(result), "(R(json), R(os.path.path), R(os.path), R(json.dumps), R(json.loads))")
assert_eq(calls, [("json", "dict", "dict", None, 0, {}), ("os.path", "dict", "dict", None, 0, {}),
                  ("os.path", "dict", "dict", None, 0, {}), ("json", "dict", "dict", ("dumps", "loads"), 0, {})])
assert_eq(run("lazy import json", __lazy_import__=None), (("ImportError", "__lazy_import__ not found"), []))
assert_eq(run("lazy import json", __lazy_import__=5), (("TypeError", "'int' object is not callable"), []))

listed = "import json\nfrom os import sep\nimport math\nr = (json, sep, math)"
result, calls = run(listed, Listing, __lazy_import__=hook, __import__=eager)
assert_eq(repr(result), "(R(json), R(os.sep), R(E:math))")
assert_eq(calls, ["read", ("json", "Listing", "Listing", None, 0, {}), "read", ("os", "Listing", "Listing", ("sep",), 0, {}),
                  "read", ("eager", "math", None)])
