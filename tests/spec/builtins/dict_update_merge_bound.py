# spec: PLS-315 26.1.3, 13.2.3
# description: dict.update of a dict merged into a dict holding entries
# compares a colliding key by its Python __eq__, which may loop, with no
# __hash__ call, whether update is read from a dict held in a closure, a
# list or an attribute, kept aside as a bound method, or called again in a
# loop; an exception from __eq__ propagates, the entries before it merged.
from harness import *

log = []
class Key:
    def __init__(self, n): self.n = n
    def __hash__(self): log.append(("hash", self.n)); return 0
    def __eq__(self, other):
        for _ in range(2): pass
        log.append(("eq", self.n, other.n))
        if self.n < 0: raise LookupError(self.n)
        return self.n == other.n

def shown(d): return sorted((k.n, v) for k, v in d.items())
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
class Holder: pass
def cases():
    d = {Key(1): "a"}
    box = [d]
    h = Holder(); h.d = d
    def closure(): d.update({Key(1): "b"}); return shown(d)
    def listed(): box[0].update({Key(2): "c"}); return shown(d)
    def held(): u = h.d.update; u({Key(1): "d"}); return shown(d)
    def loop():
        for i in range(2): d.update({Key(2): i})
        return shown(d)
    def failing():
        e = {Key(-1): 0}
        e.update({Key(3): 1}); return shown(e)
    return [run(closure), run(listed), run(held), run(loop), run(failing)]
expected = [([(1, "b")], [("hash", 1), ("eq", 1, 1)]), ([(1, "b"), (2, "c")], [("hash", 2), ("eq", 1, 2)]),
            ([(1, "d"), (2, "c")], [("hash", 1), ("eq", 1, 1)]), ([(1, "d"), (2, 1)], [("hash", 2), ("eq", 1, 2), ("eq", 2, 2)] * 2),
            (("LookupError", "-1"), [("hash", -1), ("hash", 3), ("eq", -1, 3)])]
assert_eq(cases(), expected)
assert_eq(cases(), expected)
