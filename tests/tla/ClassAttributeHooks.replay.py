# Replays ClassAttributeHooks.tla: each case makes a metaclass with the
# spec's hooks and a class of it, performs the steps, and compares the log,
# the results, and whether the attribute remains with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def metaclass(p, log):
    namespace = {}
    if p["setattr"] == "defer":
        def __setattr__(cls, name, value):
            log.append("set")
            super(M, cls).__setattr__(name, value)
        namespace["__setattr__"] = __setattr__
    elif p["setattr"] == "refuse":
        def __setattr__(cls, name, value):
            log.append("set")
            raise AttributeError(name)
        namespace["__setattr__"] = __setattr__
    if p["delattr"] == "defer":
        def __delattr__(cls, name):
            log.append("del")
            super(M, cls).__delattr__(name)
        namespace["__delattr__"] = __delattr__
    elif p["delattr"] == "refuse":
        def __delattr__(cls, name):
            log.append("del")
            raise AttributeError(name)
        namespace["__delattr__"] = __delattr__
    M = type("M", (type,), namespace)
    return M


def outcome(p):
    log = []
    C = metaclass(p, log)("C", (), {})
    results = ""
    for op in p["steps"]:
        try:
            if op == "set":
                C.a = 1
            else:
                del C.a
            results += "ok "
        except AttributeError:
            results += "AttributeError "
    return {"log": "".join(word + " " for word in log), "results": results, "present": "a" in C.__dict__}


check_programs(outcome)
