# Replays Lists.tla: each case builds the spec's list or bytearray, applies
# the operation, and compares what it returns and the items afterwards,
# or the exception, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


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
            s[p["i"]] = 7
        elif op == "del":
            del s[p["i"]]
        elif op == "setslice":
            s[arg(p["start"]):arg(p["stop"]):arg(p["step"])] = t
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
            s.insert(p["i"], 7)
        elif op == "pop":
            return ("item", s.pop() if p["i"] == 99 else s.pop(p["i"]), tuple(s))
        else:
            s.remove(p["x"])
    except (IndexError, ValueError) as error:
        return (type(error).__name__, 0, ())
    return ("None", 0, tuple(s))


check_programs(outcome)
