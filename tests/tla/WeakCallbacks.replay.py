# Replays WeakCallbacks.tla: each case drops the spec's object with a
# looping weak-reference callback and compares the log with the model's.
from harness import host

host.disable_automatic_collection()

FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

log = []


class Plain:
    pass


class Finalized:
    def __del__(self):
        for _ in range(2):
            pass
        log.append("del")


def callback(name, held, fails):
    def called(ref):
        for _ in range(2):
            pass
        if ref() is None:
            log.append(name)
        if held:
            held.pop()
        if fails:
            raise LookupError(name)
    return called


def drop(p):
    target = (Finalized if p["finalizer"] else Plain)()
    held = [Plain()] if p["chains"] else []
    refs = [host.weak_reference(target, callback("callback", held, p["fails"]))]
    if held:
        refs.append(host.weak_reference(held[0], callback("second", None, False)))
    if p["cyclic"]:
        target.me = target
    del target
    if p["cyclic"]:
        host.collect()
    log.append("after")
    yield refs


def outcome(p):
    del log[:]
    if p["place"] == "function":
        list(drop(p))
    else:
        steps = drop(p)
        next(steps)
        steps.close()
    return tuple(log)


check_programs(outcome)
