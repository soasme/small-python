# Replays KeywordHashes.tla: each case merges the spec's ** dicts, whose
# keys are a logging str subclass's, into its target, and compares the
# result's items in order and the log of __hash__ and __eq__ calls, or the
# TypeError, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

log = []


class Name(str):
    def __hash__(self):
        log.append("hash")
        return str.__hash__(self)

    def __eq__(self, other):
        log.append("eq")
        return str.__eq__(self, other)


class D(dict):
    pass


class F(frozendict):
    pass


def f(**kw):
    return kw


def outcome(p):
    first = {"a": 0} if p["explicit"] else {}
    sources = [{Name(k): i} for i, k in enumerate(p["keys"], 1)]
    del log[:]
    try:
        if p["target"] == "display":
            result = {**first, **sources[0], **(sources[1] if len(sources) > 1 else {})}
        elif p["target"] == "update":
            result = {}
            result.update(**first, **sources[0], **(sources[1] if len(sources) > 1 else {}))
        else:
            callee = {"call": f, "dict": dict, "dict subclass": D, "frozendict": frozendict, "frozendict subclass": F}[p["target"]]
            result = callee(**first, **sources[0], **(sources[1] if len(sources) > 1 else {}))
    except TypeError:
        return ("TypeError", (), tuple(log))
    return ("ok", tuple((str(k), v) for k, v in result.items()), tuple(log))


check_programs(outcome)
