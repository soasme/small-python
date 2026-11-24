# spec: PLS-315 16.4.1, 9.3.1, 26.1.3
# description: A class statement looks up __build_class__ in its builtins
# dict, first comparing a stored key of the name's hash by its Python
# __eq__, which may loop: an equal key's value is the builder; a dict
# subclass's __missing__ is called only after no key was equal; an error
# from __eq__ propagates; with neither, NameError. The builder is called
# with every base, more than eight too.
from harness import *

log = []
real = __build_class__
class Key:
    def __init__(self, equal): self.equal = equal
    def __hash__(self): return hash("__build_class__")
    def __eq__(self, other):
        for _ in range(2): pass
        # How often a probe compares the same key is not specified.
        if ("eq", other) not in log: log.append(("eq", other))
        if self.equal is None: raise ValueError("eq")
        return self.equal
def builder(func, name, *bases, **kw):
    for _ in range(2): pass
    log.append(("build", name, len(bases)))
    return real(func, name, *bases, **kw)
class Missing(dict):
    def __missing__(self, key):
        for _ in range(2): pass
        log.append(("missing", key))
        return builder
def run(builtins, source="class A: pass"):
    del log[:]
    try:
        g = {"__builtins__": builtins, "__name__": "m"}
        exec(source, g)
        r = g["A"].__name__
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
assert_eq(run({"__build_class__": builder, Key(False): 0}), ("A", [("build", "A", 0)]))
assert_eq(run({Key(True): builder}), ("A", [("eq", "__build_class__"), ("build", "A", 0)]))
assert_eq(run({Key(None): builder}), (("ValueError", "eq"), [("eq", "__build_class__")]))
assert_eq(run({Key(False): builder}), (("NameError", "__build_class__ not found"), [("eq", "__build_class__")]))
assert_eq(run(Missing({Key(False): 0})), ("A", [("eq", "__build_class__"), ("missing", "__build_class__"), ("build", "A", 0)]))
assert_eq(run(Missing({Key(True): builder})), ("A", [("eq", "__build_class__"), ("build", "A", 0)]))
class B: pass
bases = {"__builtins__": {"__build_class__": builder}, "__name__": "m", "bs": [type("C%d" % i, (B,), {}) for i in range(12)]}
del log[:]
exec("class A(*bs): pass", bases)
assert_eq(log, [("build", "A", 12)])
