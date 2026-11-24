# spec: PLS-315 9.3.1, 9.3.2, 26.1.3
# description: A name looked up in a dict subclass namespace with a
# __missing__, as builtins, globals read as locals, or explicit locals,
# first compares a stored key of the name's hash by its Python __eq__,
# which may loop: an equal key's value is the name's, and __missing__ is
# called only after no key was equal; an error from __eq__ propagates.
# (How often a probe compares the same key is not specified.)
from harness import *

log = []
class Key:
    def __init__(self, equal): self.equal, self.seen = equal, False
    def __hash__(self): return hash("abc")
    def __eq__(self, other):
        for _ in range(2): pass
        if not self.seen: log.append(("eq", other))
        self.seen = True
        if self.equal is None: raise ValueError("eq")
        return self.equal
class Missing(dict):
    def __missing__(self, key):
        for _ in range(2): pass
        log.append(("missing", key))
        return "missing:" + key
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def ns(equal): return Missing({Key(equal): "stored"})
cases = [lambda: eval("abc", {}, ns(False)), lambda: eval("abc", {}, ns(True)), lambda: eval("abc", {}, ns(None)),
         lambda: eval("abc", ns(False)), lambda: eval("abc", ns(True)),
         lambda: eval("abc", {"__builtins__": ns(False)}), lambda: eval("abc", {"__builtins__": ns(True)}),
         lambda: eval("[abc for _ in [1]]", {"__builtins__": ns(False)})]
assert_eq([run(f) for f in cases],
          [("missing:abc", [("eq", "abc"), ("missing", "abc")]), ("stored", [("eq", "abc")]),
           (("ValueError", "eq"), [("eq", "abc")]),
           ("missing:abc", [("eq", "abc"), ("missing", "abc")]), ("stored", [("eq", "abc")]),
           ("missing:abc", [("eq", "abc"), ("missing", "abc")]), ("stored", [("eq", "abc")]),
           (["missing:abc"], [("eq", "abc"), ("missing", "abc")])])
