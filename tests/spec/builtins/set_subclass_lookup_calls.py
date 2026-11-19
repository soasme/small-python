# spec: PLS-315 26.3.2 26.3.3 7.5.7
# description: add, discard and remove of a set subclass's instance hash
# their element by its Python __hash__, then look it up in the set's
# entries as an exact set's do, calling an entry's Python __eq__ with the
# element on a matching hash, in order: an equal entry is kept, not
# added twice, or removed; remove of a missing element raises KeyError
# naming it, and an error of __eq__ propagates, leaving the set as it was.
from harness import *

log = []
class B:
    def __init__(self, v): self.v = v
    def __hash__(self):
        for _ in (): pass
        log.append(("hash", self.v))
        return 1
    def __eq__(self, other):
        for _ in (): pass
        log.append(("eq", self.v, other.v))
        if other.v < 0: raise LookupError("eq")
        return self.v == other.v

class Sub(set): pass

def attempt(f):
    try: return f()
    except Exception as e: return (type(e).__name__, type(e.args[0]).__name__ if e.args else None)

def results():
    for _ in (): pass
    del log[:]
    s = Sub()
    s.add(B(0)); s.add(B(1)); s.add(B(1))
    s.discard(B(0))
    missing = attempt(lambda: s.remove(B(5)))
    failed = attempt(lambda: s.add(B(-1)))
    return [len(s), sorted(x.v for x in s), missing, failed], list(log)

expected = ([1, [1], ("KeyError", "B"), ("LookupError", "str")],
            [("hash", 0), ("hash", 1), ("eq", 0, 1), ("hash", 1), ("eq", 0, 1), ("eq", 1, 1),
             ("hash", 0), ("eq", 0, 0), ("hash", 5), ("eq", 1, 5), ("hash", -1), ("eq", 1, -1)])

assert_eq(results(), expected)
assert_eq(results(), expected)
