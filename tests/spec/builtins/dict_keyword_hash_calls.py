# spec: PLS-315 26.1.1, 26.2
# description: dict() and frozendict() given keywords whose names are str
# subclass instances store each name in order by its hash, a Python
# __hash__ that may loop called once per name, and by equality with the
# names stored before it of equal hash, a Python __eq__ deciding: a true
# result stores the value under the first name, a false one keeps both.
# An exception from __hash__ or __eq__, or a __hash__ returning no int,
# fails the call. After a positional mapping's items as alone. Inside
# functions and generators as at module level.
from harness import *

log = []
# What each name's __eq__ returns once armed: by the first __hash__ of a
# call's names, after the call's ** merged them with their stored hashes.
armed = []
answers = {"t": True, "r": "raise"}

class Name(str):
    def __hash__(self):
        for _ in range(2): pass
        if not armed: return 7
        armed[0] = 1
        log.append(("hash", str(self)))
        if str(self) == "nohash": return "x"
        if str(self) == "badhash": raise LookupError("hash")
        return 7
    def __eq__(self, other):
        for _ in range(2): pass
        if not armed or not armed[0]: return False
        log.append(("eq", str(self), str(other)))
        answer = answers.get(str(self), False)
        if answer == "raise": raise KeyError(str(self))
        return answer

def items(d):
    return sorted((type(k).__name__, str(k), v) for k, v in d.items())

def run(make, *names):
    keywords = {n: i for i, n in enumerate(names)}
    del log[:]
    armed.append(0)
    try:
        r = items(make(keywords))
    except Exception as e:
        r = type(e).__name__
    armed.pop()
    return r, list(log)

def results():
    out = []
    for make in (lambda k: dict(**k), lambda k: frozendict(**k), lambda k: dict([("z", 9)], **k)):
        out.append(run(make, Name("a")))
        out.append(run(make, Name("a"), Name("b")))
        out.append(run(make, Name("a"), Name("t")))
        out.append(run(make, Name("a"), Name("r")))
        out.append(run(make, Name("a"), Name("nohash")))
        out.append(run(make, Name("badhash")))
    return out

def expected():
    out = []
    for z in ([], [], [("str", "z", 9)]):
        out.append((sorted(z + [("Name", "a", 0)]), [("hash", "a")]))
        out.append((sorted(z + [("Name", "a", 0), ("Name", "b", 1)]), [("hash", "a"), ("hash", "b"), ("eq", "a", "b")]))
        out.append((sorted(z + [("Name", "a", 0), ("Name", "t", 1)]), [("hash", "a"), ("hash", "t"), ("eq", "a", "t")]))
        out.append((sorted(z + [("Name", "a", 0), ("Name", "r", 1)]), [("hash", "a"), ("hash", "r"), ("eq", "a", "r")]))
        out.append(("TypeError", [("hash", "a"), ("hash", "nohash")]))
        out.append(("LookupError", [("hash", "badhash")]))
    return out

assert_eq(results(), expected())

def inside():
    return results()
assert_eq(inside(), expected())

def gen():
    yield results()
assert_eq(next(gen()), expected())
