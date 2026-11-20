# Replays Slices.tla: each case makes the spec's slice and compares the
# result of the operation with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class Indexed:
    def __init__(self, name, log, value=3):
        self.name, self.log, self.value = name, log, value

    def __index__(self):
        for _ in ():  # a loop: __index__ runs on the machine
            pass
        self.log.append(self.name)
        return self.value

    def __repr__(self):
        return "I3"


class Sub(int):
    def __index__(self):
        raise AssertionError("an int subclass is its int")


def value(v, name, log):
    return None if v == 99 else "x" if v == 98 else Indexed(name, log) if v == 97 else Sub(3) if v == 96 else v


class Part:
    def __init__(self, value, log):
        self.value, self.log = value, log

    def __eq__(self, other):
        for _ in ():  # a loop: the method runs on the machine
            pass
        self.log.append("eq")
        if self.value == "raise":
            raise KeyError(self.value)
        return self.value == other.value

    def __lt__(self, other):
        for _ in ():
            pass
        self.log.append("lt")
        return self.value < other.value

    __hash__ = None


def compared(p):
    log = []

    def made(value):
        parts = [None, None, None]
        parts[p["part"] - 1] = Part(value, log)
        return slice(*parts)

    left, right = ("raise", 1) if p["other"] == "raise" else (1, 1 if p["other"] == "one" else 2)
    try:
        result = repr(made(left) == made(right) if p["rel"] == "eq" else made(left) < made(right))
    except KeyError:
        result = "KeyError"
    return " ".join([result] + log)


def outcome(p):
    if p["op"] == "compare":
        return compared(p)
    if p["op"] == "generic":
        return repr(slice[float])
    log = []
    s = slice(value(p["start"], "start", log), value(p["stop"], "stop", log), value(p["step"], "step", log))
    return "".join([result(p, s, log)] + [" " + name for name in log])


def result(p, s, log):
    op = p["op"]
    try:
        if op == "indices":
            return repr(s.indices(p["length"]))
        if op == "lengthed":
            return repr(s.indices(Indexed("length", log, p["length"])))
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
