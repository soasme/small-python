# Replays With.tla: each case runs a with statement over the spec's
# managers and compares the methods' log and the ending with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def manager(log, name, enter, exit, suffix=""):
    body = {}
    if enter != "missing":
        def __enter__(self):
            log.append("enter" + suffix)
            if enter == "raise":
                raise ValueError
            return self
        body["__enter__"] = __enter__
    if exit != "missing":
        def __exit__(self, kind, value, traceback):
            log.append("exit%s:%s" % (suffix, "None" if kind is None else kind.__name__))
            if exit == "raise":
                raise RuntimeError
            return exit == "true"
        body["__exit__"] = __exit__
    return type(name, (), body)()


def single(p, log):
    m = manager(log, "M", p["enter"], p["exit"])
    with m:
        log.append("body")
        if p["body"] == "raise":
            raise KeyError
        if p["body"] == "return":
            return "returned"
    return "done"


def nested(p, log):
    with manager(log, "M", "ok", p["exit"], "M"), manager(log, "N", "raise", "false", "N"):
        pass
    return "done"


def outcome(p):
    log = []
    try:
        end = single(p, log) if p["part"] == "single" else nested(p, log)
    except (TypeError, ValueError, KeyError, RuntimeError) as error:
        end = type(error).__name__
    return " ".join(log + [end])


check_programs(outcome)
