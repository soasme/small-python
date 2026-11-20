# spec: PLS-315 26.6, 7.2.4
# description: x in mappingproxy(m) is x in m: a mapping's Python
# __contains__, which may loop or raise, an iterable's __iter__ without
# one, and its keys' Python __eq__; not in inverts it and a chain keeps
# the proxy as its next operand.
from harness import *

MP = type(type.__dict__)
log = []
class M(dict):
    def __contains__(self, k):
        for _ in (): pass
        log.append(k)
        if k == "raise": raise LookupError("c")
        return k == "magic" or dict.__contains__(self, k)
class G:
    def __getitem__(self, k): return 1
    def keys(self): return []
    def __iter__(self):
        for _ in (): pass
        log.append("iter")
        return iter(["it"])
class H:
    def __init__(self, v): self.v = v
    def __hash__(self): return 1
    def __eq__(self, o):
        for _ in (): pass
        log.append(("eq", self.v))
        return isinstance(o, H)
def t(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return (r, log[:])

v = MP(M({"key": 1}))
assert_eq([t(lambda: "key" in v), t(lambda: "magic" in v), t(lambda: "xxx" not in v), t(lambda: "raise" in v)],
          [(True, ["key"]), (True, ["magic"]), (True, ["xxx"]), (("LookupError", "c"), ["raise"])])
assert_eq([t(lambda: 1 < 2 and "key" in v in [True]), t(lambda: "key" in v in [False])], [(False, ["key"]), (False, ["key"])])
assert_eq([t(lambda: "x" in MP({"x": 1})), t(lambda: "it" in MP(G())), t(lambda: [k in v for k in ("key", "no")])],
          [(True, []), (True, ["iter"]), ([True, False], ["key", "no"])])
def f(): return "magic" in v, "q" in v
assert_eq(t(f), ((True, False), ["magic", "q"]))
assert_eq([t(lambda: H(1) in MP({H(2): 0})), t(lambda: 5 in MP({}))], [(True, [("eq", 2)]), (False, [])])
assert_eq(t(lambda: [1] in MP({})), (("TypeError", "cannot use 'list' as a dict key (unhashable type: 'list')"), []))
assert_eq([t(lambda: "a" in type.__dict__), t(lambda: "__dict__" in H.__dict__), t(lambda: "x" in MP(MP({"x": 1})))],
          [(False, []), (True, []), (True, [])])
