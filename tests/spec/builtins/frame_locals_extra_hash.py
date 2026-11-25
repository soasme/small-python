# spec: PLS-315 28.3, 26.1
# description: a frame locals proxy hashes a key once to look for a
# variable, then its extra locals' dictionary hashes it again: a TypeError
# from that second hash is the dictionary's, "cannot use ... as a dict
# key (...)", while any other exception propagates as raised.
from harness import assert_eq

class Second:
    def __init__(self, bad): self.calls, self.bad = 0, bad
    def __hash__(self):
        for _ in (): pass
        self.calls += 1
        if self.calls == 2:
            if self.bad == "raise": raise KeyError("second")
            if self.bad == "type": raise TypeError("mine")
            return "no"
        return hash("q")
    def __eq__(self, other): return isinstance(other, Second)

def suspended():
    a = 1
    yield

g = suspended(); next(g)
p = g.gi_frame.f_locals
p["extra"] = 1

def attempt(op, bad):
    k = Second(bad)
    try: return op(k)
    except Exception as e: return type(e).__name__, str(e), k.calls

ops = [lambda k: p[k], lambda k: k in p, lambda k: p.get(k), lambda k: p.__setitem__(k, 2)]
assert_eq([attempt(op, "raise") for op in ops],
          [("KeyError", "'second'", 2), ("KeyError", "'second'", 2), None, ("KeyError", "'second'", 2)])
message = "cannot use 'Second' as a dict key (__hash__ method should return an integer)"
assert_eq([attempt(op, "int") for op in ops], [("TypeError", message, 2)] * 4)
assert_eq(attempt(ops[0], "type"), ("TypeError", "cannot use 'Second' as a dict key (mine)", 2))
assert_eq(sorted(k for k in p if isinstance(k, str)), ["a", "extra"])
