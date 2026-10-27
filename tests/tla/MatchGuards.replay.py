# Replays MatchGuards.tla: each case matches t(x) against the spec's case
# blocks, logging the subject, value pattern lookups, guards, and suites, and
# compares n and the log with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

PATTERNS = {"one": "1", "capture": "n", "value": "C.two", "group": "(1 | 2)"}
PRE = """log = []
def t(v):
    log.append('subject')
    return v
def g(i, v):
    log.append('guard %d' % i)
    return v
class Values:
    @property
    def two(self):
        log.append('C.two')
        return 2
C = Values()
n = None
"""


def outcome(p):
    lines = ["match t(%d):" % p["subject"]]
    for k, block in enumerate(p["cases"], 1):
        guard = "" if block["guard"] == "none" else " if g(%d, %s)" % (k, block["guard"] == "yes")
        lines += ["    case %s%s:" % (PATTERNS[block["pattern"]], guard), "        log.append('case %d')" % k]
    namespace = {}
    try:
        exec(compile(PRE + "\n".join(lines), "<match>", "exec"), namespace)
    except SyntaxError as error:
        return ("SyntaxError: %s" % error.msg, ())
    return (repr(namespace["n"]) if namespace["n"] is None else str(namespace["n"]), tuple(namespace["log"]))


check_programs(outcome)
