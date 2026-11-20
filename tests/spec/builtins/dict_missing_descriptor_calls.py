# spec: PLS-315 26.1.2
# description: Subscripting a dict subclass's instance with an absent key
# reads a __missing__ that a descriptor's Python __get__ gives, which may
# loop or raise, then calls it with the key, its exceptions propagating; a
# present key and the in operator read nothing.
from harness import *

log = []
class D:
    def __init__(s, f, mode=None): s.f = f; s.mode = mode
    def __get__(s, obj, owner):
        for _ in (): pass
        log.append(("get", type(obj).__name__))
        if s.mode == "attr": raise AttributeError("gone")
        if s.mode == "key": raise ValueError("v")
        return s.f.__get__(obj, owner)
def missing(self, key):
    for _ in (): pass
    log.append(("missing", key))
    if key == "raise": raise KeyError("deep")
    return len(key)
def run(f):
    del log[:]
    try: r = f()
    except BaseException as e: r = (type(e).__name__, str(e))
    return r, log[:]
def results():
    out = []
    for mode in (None, "attr", "key"):
        S = type("S", (dict,), {"__missing__": D(missing, mode)})
        d = S(a=1)
        out.append((run(lambda: d["a"]), run(lambda: d["hi"]), run(lambda: d["raise"]), run(lambda: [d["xy"], d["a"]][0] + 1), run(lambda: "hi" in d)))
    def inside():
        for _ in (): pass
        d = type("S", (dict,), {"__missing__": D(missing)})()
        return d["abc"], d.get("abc", 0)
    out.append(run(inside))
    return out

expected = [
    ((1, []), (2, [('get', 'S'), ('missing', 'hi')]), (('KeyError', "'deep'"), [('get', 'S'), ('missing', 'raise')]), (3, [('get', 'S'), ('missing', 'xy')]), (False, [])),
    ((1, []), (('AttributeError', 'gone'), [('get', 'S')]), (('AttributeError', 'gone'), [('get', 'S')]), (('AttributeError', 'gone'), [('get', 'S')]), (False, [])),
    ((1, []), (('ValueError', 'v'), [('get', 'S')]), (('ValueError', 'v'), [('get', 'S')]), (('ValueError', 'v'), [('get', 'S')]), (False, [])),
    ((3, 0), [('get', 'S'), ('missing', 'abc')]),
]
assert_eq(results(), expected)
