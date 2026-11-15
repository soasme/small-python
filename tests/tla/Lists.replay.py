# Replays Lists.tla: each case builds the spec's list or bytearray, applies
# the operation, and compares what it returns and the items afterwards,
# or the exception, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class Index:
    def __init__(self, i):
        self.i = i

    def __index__(self):
        for _ in ():  # a loop: __index__ runs on the machine
            pass
        return self.i


def parts(p, name):
    return None if p[name] == 99 else Index(p[name])


def index(p):
    return Index(p["i"]) if p["by"] == "index" else p["i"]


def arg(v):
    return None if v == 99 else v


def outcome(p):
    kind = list if p["type"] == "list" else bytearray
    s = kind(p["items"])
    op = p["op"]
    t = kind(p.get("t", ()))
    r = None
    try:
        if op == "set":
            s[index(p)] = 7
        elif op == "del":
            del s[index(p)]
        elif op == "setslice":
            s[arg(p["start"]):arg(p["stop"]):arg(p["step"])] = t
        elif op == "genslice":
            s[arg(p["start"]):arg(p["stop"]):arg(p["step"])] = (x for x in t)
        elif op == "idxslice":
            s[parts(p, "start"):parts(p, "stop"):parts(p, "step")] = t
        elif op == "idxdel":
            del s[parts(p, "start"):parts(p, "stop"):parts(p, "step")]
        elif op == "delslice":
            del s[arg(p["start"]):arg(p["stop"]):arg(p["step"])]
        elif op == "iadd":
            s += t
        elif op == "extend":
            s.extend(t)
        elif op == "imul":
            s *= p["n"]
        elif op == "append":
            s.append(7)
        elif op == "clear":
            s.clear()
        elif op == "copy":
            c = s.copy()
            if c is s or type(c) is not kind:
                return ("not a copy", 0, ())
            return ("copy", 0, tuple(c))
        elif op == "reverse":
            s.reverse()
        elif op == "insert":
            s.insert(index(p), 7)
        elif op == "pop":
            return ("item", s.pop() if p["i"] == 99 else s.pop(index(p)), tuple(s))
        else:
            s.remove(p["x"])
    except (IndexError, ValueError) as error:
        return (type(error).__name__, 0, ())
    return ("None", 0, tuple(s))


check_programs(outcome)
