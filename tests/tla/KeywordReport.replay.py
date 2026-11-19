# Replays KeywordReport.tla: each case calls sorted([]) with the program's
# keywords, str subclass instances k1 and k2 whose Python __eq__ answers as
# the program says, and counts the calls.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def outcome(p):
    calls = []

    class Key(str):
        __hash__ = str.__hash__
        def __eq__(self, other):
            # A loop puts the method's body on the machine.
            for _ in (): pass
            calls.append(other)
            answer = p[int(str(self)[1]) - 1]
            if answer == "raise":
                raise LookupError(other)
            return answer == other

    try:
        sorted([], **{Key("k" + str(i + 1)): 1 for i in range(len(p))})
    except LookupError:
        return ("LookupError", len(calls))
    except TypeError as e:
        text = str(e)
        if text == "invalid keyword argument for sort()":
            return ("invalid", len(calls))
        return ("unexpected " + text.split("'")[1], len(calls))
    return ("bound", len(calls))

check_programs(outcome)
