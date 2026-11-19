# Replays OpenFirst.tla: each case makes the program's two open() calls of
# a file the first case writes, by keyword, in the replay's first open(),
# and writes their outcomes.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

NAME = "tla_open_first.txt"


def opened(call):
    try:
        if call == "positional":
            f = open(NAME, "r")
        elif call == "keywords":
            f = open(file=NAME, mode="r")
        elif call == "mode":
            f = open(NAME, mode="q")
        else:
            f = open(NAME, colour="red")
    except (ValueError, TypeError) as e:
        return type(e).__name__
    text = f.read()
    f.close()
    return text


def outcome(p):
    return opened(p["first"]) + " / " + opened(p["second"])


first = True


def written(p):
    global first
    if first:
        first = False
        f = open(file=NAME, mode="w")
        f.write("x")
        f.close()
    return outcome(p)

check_programs(written)
