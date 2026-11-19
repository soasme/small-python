# spec: PLS-315 26.6
# description: A mappingproxy's __getitem__, get, keys, values, items and
# copy, called as methods or through the type, call its mapping's own
# Python methods, which may loop; their results and errors pass through
# unchanged. Inside functions and generators as at module level.
from harness import *

Proxy = type(type.__dict__)
log = []

class M:
    def __init__(self, d): self.d = d
    def __getitem__(self, k):
        for _ in range(2): pass
        log.append(("getitem", k))
        return self.d[k]
    def get(self, k, default=None):
        for _ in range(2): pass
        log.append(("get", k, default))
        return self.d.get(k, default)
    def keys(self):
        for _ in range(2): pass
        log.append("keys")
        return list(self.d)
    def values(self):
        for _ in range(2): pass
        log.append("values")
        return list(self.d.values())
    def items(self):
        for _ in range(2): pass
        log.append("items")
        return list(self.d.items())
    def copy(self):
        for _ in range(2): pass
        log.append("copy")
        return M(dict(self.d))

def run(f, *args):
    del log[:]
    try: r = f(*args)
    except Exception as e: r = (type(e).__name__, str(e))
    if isinstance(r, M): r = ("M", r.d)
    return r, log[:]

def cases():
    p = Proxy(M({"a": 1}))
    return [run(p.__getitem__, "a"), run(p.__getitem__, "z"), run(p.get, "a"), run(p.get, "z", 0), run(p.get, "z"),
            run(p.keys), run(p.values), run(p.items), run(p.copy), run(Proxy.get, p, "a"), run(Proxy.__getitem__, p, "a")]

expected = [(1, [("getitem", "a")]), (("KeyError", "'z'"), [("getitem", "z")]), (1, [("get", "a", None)]),
            (0, [("get", "z", 0)]), (None, [("get", "z", None)]), (["a"], ["keys"]), ([1], ["values"]),
            ([("a", 1)], ["items"]), (("M", {"a": 1}), ["copy"]), (1, [("get", "a", None)]), (1, [("getitem", "a")])]

def gen():
    yield cases()

assert_eq(cases(), expected)
assert_eq(next(gen()), expected)
def main(): return cases()
assert_eq(main(), expected)
