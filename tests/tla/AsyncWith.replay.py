# Replays AsyncWith.tla: each case drives a coroutine running async with
# (or with) over the spec's manager and compares the log, the number of
# values passed out, and the ending with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class Step:
    def __await__(self):
        yield "tick"


def drive(coro):
    out = []
    try:
        while True:
            out.append(coro.send(None))
    except StopIteration:
        result = "done"
    except (TypeError, ValueError, KeyError, RuntimeError) as error:
        result = type(error).__name__
        if "Did you mean to use 'with'" in str(error):
            result += ": use with"
        elif "Did you mean to use 'async with'" in str(error):
            result += ": use async with"
    return len(out), result


class Manager:
    def __init__(self, log, enter, exit):
        self.log, self.enter, self.exit = log, enter, exit

    async def __aenter__(self):
        self.log.append("aenter")
        await Step()
        if self.enter == "raise":
            raise ValueError
        return self

    async def __aexit__(self, kind, value, traceback):
        self.log.append("aexit:" + ("None" if kind is None else kind.__name__))
        await Step()
        if self.exit == "raise":
            raise RuntimeError
        return self.exit == "true"


class Sync:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class NoAexit:
    async def __aenter__(self):
        return self


class BadAenter:
    def __aenter__(self):
        return 5

    async def __aexit__(self, *exc):
        return False


def manager(p):
    log = []

    async def main():
        async with Manager(log, p["enter"], p["exit"]):
            log.append("body")
            if p["body"] == "raise":
                raise KeyError
    count, result = drive(main())
    return " ".join(log + [str(count), result])


def protocol(case):
    async def main():
        if case == "async":
            with Manager([], "ok", "false"):
                pass
        else:
            async with {"sync": Sync, "noaexit": NoAexit, "badaenter": BadAenter}[case]():
                pass
    count, result = drive(main())
    return "%d %s" % (count, result)


def outcome(p):
    return manager(p) if p["part"] == "manager" else protocol(p["case"])


check_programs(outcome)
