# Replays AbstractChecks.tla: each case builds the spec's objects and
# compares isinstance() or issubclass(), with the log of attribute reads,
# against the model's outcome.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

log = []


class Bases:
    def __init__(self, name, bases): self.name, self.bases = name, bases
    @property
    def __bases__(self):
        for _ in (): pass  # a loop: the property runs on the machine
        log.append(self.name)
        return self.bases


class Getattr:
    def __getattr__(self, name):
        for _ in (): pass
        log.append("getattr")
        return (A,) if name == "__bases__" else None


class Loop:
    @property
    def __bases__(self):
        for _ in (): pass
        return (self, self)


class Inst:
    def __init__(self, cls): self.cls = cls
    @property
    def __class__(self):
        for _ in (): pass
        log.append("class")
        return self.cls


class K: pass


A = Bases("A", ()); B = Bases("B", (A,)); C = Bases("C", (B, A)); D = Bases("D", (C,))
Z = Bases("Z", ()); N = object()
OBJECTS = {"A": A, "B": B, "C": C, "D": D, "Z": Z, "G": Getattr(), "N": N,
           "Loop": Loop(), "int": int, "K": K, "pair": (Z, A)}


def outcome(p):
    for _ in (): pass
    log.clear()
    s, t = OBJECTS[p["subject"]], OBJECTS[p["target"]]
    try:
        args = (s, t) if p["check"] == "issubclass" else (Inst(s), t)
        f = issubclass if p["check"] == "issubclass" else isinstance
        if p["via"] == "type":
            f = type.__subclasscheck__ if p["check"] == "issubclass" else type.__instancecheck__
            args = args[::-1]
        r = repr(f(*args) if p["via"] == "starred" else f(args[0], args[1]))
    except RecursionError:
        return "RecursionError"
    except TypeError as e:
        r = "TypeError:d" if "descriptor" in str(e) else "TypeError:" + str(e).split(" arg ")[1][0]
    return " ".join([r] + log)


check_programs(outcome)
