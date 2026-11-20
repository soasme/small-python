# Replays SeqOps.tla: each case builds the spec's sequence, applies the
# operation, and compares the result (items as 1 and 2, the characters
# of a str as "a" and "b"), or the exception, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def build(kind, items):
    if kind == "str":
        return "".join("_ab"[i] for i in items)
    if kind == "tuple":
        return tuple(items)
    if kind == "bytes":
        return bytes(items)
    if kind == "list":
        return list(items)
    return bytearray(items)


def ids(seq):
    return tuple(ord(c) - 96 if type(c) is str else c for c in seq)


class Index:
    def __init__(self, i):
        self.i = i

    def __index__(self):
        for _ in ():  # a loop: __index__ runs on the machine
            pass
        return self.i


def by(p, v):
    return Index(v) if p["by"] in ("index", "method") else v


def bound(v):
    return None if v == 99 else v


def outcome(p):
    kind = p["type"]
    s = build(kind, p["items"])
    op = p["op"]
    x = ("_ab"[p["x"]] if p["x"] < 3 else "c") if kind == "str" and "x" in p else p.get("x")
    try:
        if op == "index":
            r = s[by(p, p["i"])]
            return ("item", type(r).__name__, ids([r]))
        if op == "slice":
            r = s[bound(p["start"]):bound(p["stop"]):bound(p["step"])]
        elif op == "in":
            return ("bool", "", (int(type(s).__contains__(s, x) if p["how"] == "explicit" else x in s),))
        elif op == "count":
            return ("int", "", (s.count(*(x,)) if p["how"] == "explicit" else s.count(x),))
        elif op == "find":
            return ("int", "", (s.index(*(x,)) if p["how"] == "explicit" else s.index(x),))
        elif op == "find from":
            return ("int", "", (s.index(x, p["start"]) if p["stop"] == 99 else s.index(x, p["start"], p["stop"]),))
        elif op == "concat":
            r = s + build(kind, [2])
        elif op == "concat list":
            r = s + [2]
        elif op == "repeat":
            r = s.__mul__(by(p, p["n"])) if p["by"] == "method" else s * by(p, p["n"])
        else:
            hash(s)
            return ("hashable", "", ())
    except (IndexError, ValueError, TypeError) as error:
        return (type(error).__name__, "", ())
    return ("seq", type(r).__name__, ids(r))


check_programs(outcome)
