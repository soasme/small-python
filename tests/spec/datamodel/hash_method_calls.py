# spec: PLS-315 7.5.7, 26, 28
# description: dict.get, dict.setdefault and dict.pop, and set.add,
# set.discard and set.remove, call an instance key's Python __hash__ once
# before they look it up, a call that may run long, with the key and the
# other arguments as the call evaluated them; pop of an empty dict calls
# none; an exception from __hash__ propagates, and a result that is not an
# int raises TypeError naming the dict key or set element, through a bound
# method kept aside too, or a set's method given the set first, which is
# checked before the key is hashed, inside functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(3): pass

class Key:
    def __init__(self, tag, hash=1): self.tag = tag; self.hash = hash
    def __hash__(self):
        global key
        spin()
        log.append(self.tag)
        key = Key("other")
        if self.hash == "bad": raise KeyError(self.tag)
        return self.hash
    def __eq__(self, other): return self is other

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, getattr(e.args[0], "tag", str(e))

key = None

def results():
    global key
    del log[:]
    a, b = Key("a"), Key("b", 2)
    d = {a: "A"}
    s = {a}
    out = [d.get(a), d.get(Key("c")), d.get(b, "dflt"), d.setdefault(b, "B"), d.setdefault(b, "x"), d.pop(b), d.pop(Key("d"), "gone"),
           {}.pop(Key("e"), "empty"), error(lambda: d.pop(Key("f")))]
    key = Key("k")
    held = key
    out.append(d.setdefault(key, "K") == "K" and held in d and key not in d)
    s.add(b); s.discard(Key("g")); s.remove(a)
    out += [len(s), b in s, error(lambda: s.remove(Key("h"))), error(lambda: set().add(Key("i", "bad"))),
            error(lambda: {}.get(Key("j", "text"))), error(lambda: set().discard(Key("l", "text")))]
    get, add = d.get, s.add
    add(a)
    set.discard(s, Key("n"))
    out += [get(a), a in s, error(lambda: set.add(5, Key("m")))]
    out.append(list(log))
    return out

expected = ["A", None, "dflt", "B", "B", "B", "gone", "empty", ("KeyError", "f"), True, 1, True,
            ("KeyError", "h"), ("KeyError", "'i'"),
            ("TypeError", "cannot use 'Key' as a dict key (__hash__ method should return an integer)"),
            ("TypeError", "cannot use 'Key' as a set element (__hash__ method should return an integer)"), "A", True,
            ("TypeError", "descriptor 'add' for 'set' objects doesn't apply to a 'int' object"),
            ["a", "a", "a", "c", "b", "b", "b", "b", "d", "f", "k", "k", "other", "b", "g", "a", "b", "h", "i", "j", "l", "a", "n", "a", "a"]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
