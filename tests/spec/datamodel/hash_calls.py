# spec: PLS-315 7.5.7, 13.2.2, 13.2.3, 13.3.2, 14.2.2, 14.3, 14.7
# description: A dict or set display, a dict subscription, a store to or
# deletion of a dict item (an augmented one reading, then storing) and a
# membership test of a dict or set call an instance key's Python __hash__
# once each, its result an int (-1 becoming -2) or its exception the
# operation's, a TypeError naming the key's role. The operands are those
# evaluated before the call: rebinding a name inside __hash__ does not
# change the container.
# Methods that loop run in function statements as at module level.
from harness import *

log = []

class H:
    def __init__(self, v): self.v = v
    def __hash__(self):
        for _ in range(2): pass
        log.append(self.v)
        return self.v
    def __eq__(self, other): return isinstance(other, H) and self.v == other.v

class Wrong:
    def __hash__(self):
        for _ in range(2): pass
        return "x"

class Failing:
    def __hash__(self):
        for _ in range(2): pass
        raise KeyError("failing")

class Arity:
    def __hash__(self, extra):
        for _ in range(2): pass
        return 1

class Rebind:
    def __hash__(self):
        global table
        for _ in range(2): pass
        table = {}
        return 5
    def __eq__(self, other): return other == 5

def failures(bad, d, s):
    # Each operation in a statement of this function, not a lambda's body.
    out = []
    try: {bad: 1}
    except Exception as e: out.append((type(e).__name__, str(e)))
    try: {bad}
    except Exception as e: out.append((type(e).__name__, str(e)))
    try: d[bad]
    except Exception as e: out.append((type(e).__name__, str(e)))
    try: bad in s
    except Exception as e: out.append((type(e).__name__, str(e)))
    try: d[bad] = 1
    except Exception as e: out.append((type(e).__name__, str(e)))
    try: del d[bad]
    except Exception as e: out.append((type(e).__name__, str(e)))
    return out

def stores():
    del log[:]
    d, a, keys = {}, H(1), [H(2)]
    d[a] = 1
    d[keys[0]] = 2
    x = d[a] = 5
    d[a] += 10
    d[keys[0]] += 1
    d[H(3)] = 3
    del d[H(3)]
    return sorted(d.values()), x, list(log)

def operations():
    del log[:]
    a, b = H(1), H(2)
    d = {a: "a", b: "b"}
    s = {a, b, H(1)}
    out = [d[a], [d[H(2)]][0], a in d, H(3) in d, H(4) not in s, len(s), len({a: 1, H(1): 2})]
    if b in s: out.append("in")
    out.append(hash(H(-1)) == -2 and {H(-1): 1}[H(-1)])
    out.append(d[(lambda: a)()])
    for bad in (Wrong(), Failing(), Arity()):
        out += failures(bad, d, s)
    out += failures(H(9), d, s)
    out.append(list(log))
    return out

roles = ("dict key", "set element", "dict key", "set element", "dict key", "dict key")
expected = ["a", "b", True, False, True, 2, 1, "in", 1, "a"] + \
    [("TypeError", "cannot use 'Wrong' as a %s (__hash__ method should return an integer)" % role)
     for role in roles] + [("KeyError", "'failing'")] * 6 + \
    [("TypeError", "cannot use 'Arity' as a %s (Arity.__hash__() missing 1 required positional argument: 'extra')" % role)
     for role in roles] + \
    [("KeyError", "<H>"), [1, 2, 1, 2, 1, 1, 2, 1, 3, 4, 1, 1, 2, -1, -1, -1, 1, 9, 9, 9, 9, 9, 9]]

def keyed(out):
    # The KeyError's text names the key object; compare its class only.
    out[-2] = ("KeyError", "<H>") if out[-2][0] == "KeyError" and "H object" in out[-2][1] else out[-2]
    return out

assert_eq(keyed(operations()), expected)
assert_eq(keyed(operations()), expected)

table = {5: "five"}
assert_eq(table[Rebind()], "five")
def rebound():
    global table
    table = {5: "again"}
    return table[Rebind()], table
assert_eq(rebound(), ("again", {}))
assert_eq(stores(), ([3, 15], 5, [1, 2, 1, 1, 1, 2, 2, 3, 3]))
assert_eq(stores(), ([3, 15], 5, [1, 2, 1, 1, 1, 2, 2, 3, 3]))
