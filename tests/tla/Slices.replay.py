# Replays Slices.tla: each case makes the spec's slice and compares the
# result of the operation with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def value(v):
    return None if v == 99 else "x" if v == 98 else v


def outcome(p):
    if p["op"] == "generic":
        return repr(slice[float])
    s = slice(value(p["start"]), value(p["stop"]), value(p["step"]))
    op = p["op"]
    try:
        if op == "indices":
            return repr(s.indices(p["length"]))
        if op == "subscript":
            return repr(list(range(p["length"]))[s])
        if op == "attrs":
            return " ".join(repr(x) for x in (s.start, s.stop, s.step))
        if op == "set":
            s.start = 1
            return "set"
        copy = slice(s.start, s.stop, s.step)
        return repr(s == copy and hash(s) == hash(copy))
    except (TypeError, ValueError, AttributeError) as error:
        return type(error).__name__


check_programs(outcome)
