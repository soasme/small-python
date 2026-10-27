# Replays Match.tla: each case runs the spec's match statement and compares
# which case matched, and what it bound, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

NAMES = "abnrstx"


class P:
    __match_args__ = ("x", "y")
    x, y = 1, 2

    def __repr__(self):
        return "P"


def outcome(p):
    subject, first, second = p
    source = (f"match {'P()' if subject == 'P' else subject}:\n"
              f"    case {first}:\n        which = 'case 1'\n"
              f"    case {second}:\n        which = 'case 2'\n")
    try:
        code = compile(source, "<program>", "exec")
    except SyntaxError:
        return ("syntax", ())
    namespace = {"P": P, "which": "none"}
    try:
        exec(code, namespace)
    except TypeError:
        return ("TypeError", ())
    which = namespace["which"]
    if which == "none":
        return ("none", ())
    # Only the names the matching pattern binds: a failed case may leave
    # some bound.
    pattern = first if which == "case 1" else second
    bound = [n for n in NAMES if n in namespace and n in pattern.replace("'k'", "").replace("'j'", "")]
    return (which, tuple((n, repr(namespace[n])) for n in bound))


failures = 0
count = 0
for walk in walks():
    count += 1
    steps = states(walk)
    program = next(steps)["program"]
    for state in steps:
        actual = outcome(program)
        if actual != state["outcome"]:
            failures += 1
            if failures <= 20:
                print("MISMATCH", program, "expected", state["outcome"], "got", actual)
if failures:
    print(failures, "mismatches")
else:
    print("replayed", count, "cases")
