# Replays ReduceFirst.tla: each case makes the program's two reductions of
# a fresh instance and writes their outcomes; the first case's first one is
# the first reduction of the replay's program.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def outcome(p):
    class Point:
        def __getstate__(self):
            # A loop puts the method's body on the machine.
            for _ in (): pass
            if p["fails"]:
                raise LookupError
            return {"x": 1}

    def reduce(call):
        try:
            if call == "reduce_ex":
                return Point().__reduce_ex__(2)[0].__name__ + " state"
            if call == "reduce":
                return Point().__reduce__()[0].__name__ + " state"
            Point().__getstate__()
            return "state"
        except LookupError:
            return "LookupError"

    return reduce(p["first"]) + " / " + reduce(p["second"])

check_programs(outcome)
