# Replays GeneratorLocals.tla: each case ends a generator holding a noted
# local, keeping what the program keeps, and compares when the local is
# released and whether a weak reference to the generator dies.
from harness import host

FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

released = []


class Noted:
    def __del__(self): released.append(True)


def leaf():
    yield 1


def outcome(p):
    ending = p["ending"]

    def gen():
        local = Noted()
        if ending == "refused":
            yield from leaf()
        else:
            yield 1
        if ending == "return":
            return
        raise ValueError

    released[:] = []
    g = gen()
    frame = g.gi_frame if p["keep_frame"] else None
    next(g)
    kept = None
    try:
        if ending == "throw":
            g.throw(KeyError)
        elif ending == "refused":
            g.throw(1)
        else:
            next(g)
    except Exception as e:
        if p["keep_exception"]:
            kept = e
    at_end = bool(released)
    weak = host.weak_reference(g)
    del g
    generator_dead = weak() is None
    del frame, kept
    return {"at_end": at_end, "after_drop": bool(released), "generator_dead": generator_dead}


check_programs(outcome)
