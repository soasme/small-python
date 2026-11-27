# Replays StringMixing.tla: each case compiles  x = <literals>  and gives
# its SyntaxError's message and the literals its location spans, a number
# one past the last for the token after them.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SPELLING = {"str": "'s'", "bytes": "b'b'", "t": "t't'"}


def outcome(p):
    kinds = [p["first"], p["second"]] + ([p["third"]] if p["third"] != "none" else [])
    starts, source = [], "x ="
    for kind in kinds:
        source += " "
        starts.append(len(source) + 1)
        source += SPELLING[kind]
    ends = [start + len(SPELLING[kind]) for start, kind in zip(starts, kinds)]
    try:
        compile(source, "<mixed>", "exec")
    except SyntaxError as e:
        first = starts.index(e.offset) + 1 if e.offset in starts else len(kinds) + 1
        last = ends.index(e.end_offset) + 1 if e.end_offset in ends else first
        return (e.msg, first, last)
    return ("ok", 0, 0)


check_programs(outcome)
