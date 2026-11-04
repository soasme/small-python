# Replays With.tla: each case runs a with statement over the spec's
# managers and compares the methods' log and the ending with the model's;
# an exception records whether it is reported at the with line or, for the
# body's, at its raise; a generator body runs after one suspension.
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


def single_gen(p, log):
    m = manager(log, "M", p["enter"], p["exit"])
    with m:
        yield
        log.append("body")
        if p["body"] == "raise":
            raise KeyError
        if p["body"] == "return":
            return "returned"
    return "done"


def drive(g):
    try:
        while True:
            next(g)
    except StopIteration as stop:
        return stop.value


def nested(p, log):
    with manager(log, "M", "ok", p["exit"], "M"), manager(log, "N", "raise", "false", "N"):
        pass
    return "done"


def outcome(p):
    log = []
    try:
        if p["part"] == "nested":
            end = nested(p, log)
        else:
            end = single(p, log) if p["frame"] == "function" else drive(single_gen(p, log))
    except (TypeError, ValueError, KeyError, RuntimeError) as error:
        end = type(error).__name__
        generator = p.get("frame") == "generator"
        code = single_gen.__code__ if generator else single.__code__
        tb = error.__traceback__
        while tb and tb.tb_frame.f_code is not code:
            tb = tb.tb_next
        line = tb.tb_lineno - code.co_firstlineno if tb else None
        if isinstance(error, RuntimeError) and line == 2:
            end += " at with"
        if isinstance(error, KeyError) and line == 5 + generator:
            end += " at raise"
    return " ".join(log + [end])


check_programs(outcome)
