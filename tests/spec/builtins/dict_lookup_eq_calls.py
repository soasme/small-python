# spec: PLS-315 26.1.3
# description: a dict's get, setdefault and pop of a plain str key compare
# it with a stored str-subclass key by that key's Python __eq__, once per
# lookup reaching it, in a direct call, a bound method, map() and filter();
# an error from __eq__ propagates and leaves the dict unchanged.
from harness import *

log = []

class Key(str):
    def __eq__(self, other):
        for _ in (): pass
        log.append(str(other))
        if other == "bad": raise LookupError("eq")
        return str.__eq__(self, other)
    __hash__ = str.__hash__

def run():
    d = {"a": 1, Key("k"): 2}
    out = [d.get("k"), d.get("k", 0), d.setdefault("k", 9)]
    get = d.get
    out.append(get("k"))
    out.append(list(map(d.get, ["k", "a"])))
    out.append(list(filter(d.get, ["k", "z"])))
    out.append(d.pop("k"))
    out.append(d.pop("k", 5))
    return out

assert_eq(run(), [2, 2, 2, 2, [2, 1], ["k"], 2, 5])
assert_eq(log, ["k", "k", "k", "k", "k", "k", "k"])
del log[:]
bad = {Key("bad"): 1}
assert_eq(hash("bad"), hash(Key("bad")))
assert_raises(LookupError, bad.get, "bad")
assert_raises(LookupError, bad.pop, "bad")
assert_eq(len(bad), 1)
assert_eq(log, ["bad", "bad"])
