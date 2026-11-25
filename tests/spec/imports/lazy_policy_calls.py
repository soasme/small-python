# spec: PLS-315 17.5, B.1.4
# description: an import at module level tests its module's name with
# `in` against __lazy_modules__, a container whose Python __contains__
# may loop, then, when it is lazy, asks the host's lazy-import policy,
# a Python function given the importer's __name__, the absolute name and
# the from-list (None for import); the truth of its verdict, by a Python
# __bool__ or __len__, decides, and a __bool__ returning a non-bool
# raises TypeError. Each in order, before the next module, at module
# level of exec() run from a function, a generator, and module level.
from harness import *

log = []
class Listed:
    def __init__(self, *names): self.names = names
    def __contains__(self, name):
        for _ in (): pass
        log.append(("in", name))
        return name in self.names
class Verdict:
    def __init__(self, v): self.v = v
    def __bool__(self):
        for _ in (): pass
        log.append(("bool", self.v))
        return self.v
class Sized:
    def __init__(self, n): self.n = n
    def __len__(self):
        for _ in (): pass
        log.append(("len", self.n))
        return self.n
verdicts = {}
def policy(importer, name, fromlist):
    for _ in (): pass
    log.append(("policy", importer, name, fromlist))
    return verdicts.get(name, True)

def run(source, listed):
    g = {"__name__": "m", "__lazy_modules__": listed}
    del log[:]
    try:
        exec(source, g)
        result = sorted(k for k in g if not k.startswith("__"))
    except Exception as e:
        result = (type(e).__name__, str(e))
    return result, list(log)

def cases():
    out = [run("import nowhere_a, nowhere_b\nfrom nowhere_c import x", Listed("nowhere_a", "nowhere_c"))]
    host.set_lazy_import_policy(policy)
    try:
        verdicts.update(nowhere_a=Verdict(True), nowhere_c=Sized(0), nowhere_d=Verdict(1), nowhere_e=0, nowhere_f=Sized(2))
        out += [run("import nowhere_a\nfrom nowhere_c import x, y", Listed("nowhere_a", "nowhere_c")),
                run("import nowhere_d", Listed("nowhere_d")), run("import nowhere_e", ["nowhere_e"]),
                run("from nowhere_f import z", Listed("nowhere_f")), run("lazy import nowhere_a", Listed())]
    finally:
        host.set_lazy_import_policy(None)
    return out

expected = [
    (('ModuleNotFoundError', "No module named 'nowhere_b'"), [('in', 'nowhere_a'), ('in', 'nowhere_b')]),
    (('ModuleNotFoundError', "No module named 'nowhere_c'"),
     [('in', 'nowhere_a'), ('policy', 'm', 'nowhere_a', None), ('bool', True),
      ('in', 'nowhere_c'), ('policy', 'm', 'nowhere_c', ('x', 'y')), ('len', 0)]),
    (('TypeError', 'Verdict.__bool__() must return a bool, not int'),
     [('in', 'nowhere_d'), ('policy', 'm', 'nowhere_d', None), ('bool', 1)]),
    (('ModuleNotFoundError', "No module named 'nowhere_e'"), [('policy', 'm', 'nowhere_e', None)]),
    (['z'], [('in', 'nowhere_f'), ('policy', 'm', 'nowhere_f', ('z',)), ('len', 2)]),
    (['nowhere_a'], [('policy', 'm', 'nowhere_a', None), ('bool', True)])]

def gen():
    yield cases()
def outer():
    return cases()
assert_eq(cases(), expected)
assert_eq(next(gen()), expected)
assert_eq(outer(), expected)
