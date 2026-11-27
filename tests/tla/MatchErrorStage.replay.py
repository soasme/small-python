# Replays MatchErrorStage.tla: each case compiles the module the spec
# describes and names the SyntaxError it raises by its message.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

PATTERNS = {"ok": "[a]", "names": "[a, a]", "keys": "{1: a, 1: b}", "capture": "x"}
SCOPE = "def f():\n    q = 1\n    global q\n"
NAMES = {"name 'q' is assigned to before global declaration": "scope", "'return' outside function": "return",
         "'yield' outside function": "yield", "multiple assignments to name 'a' in pattern": "names",
         "mapping pattern checks duplicate key (1)": "keys", "name capture 'x' makes remaining patterns unreachable": "capture"}


def outcome(p):
    guard = " if (yield)" if p["compile"] == "guard" else ""
    block = "return 1" if p["compile"] == "body" else "pass"
    source = ("return 1\n" if p["compile"] == "earlier" else "") + (SCOPE if p["scope"] == "before" else "")
    source += "match v:\n    case %s%s:\n        %s\n    case 2: pass\n" % (PATTERNS[p["pattern"]], guard, block)
    source += SCOPE if p["scope"] == "after" else ""
    try:
        compile(source, "<stage>", "exec")
    except SyntaxError as e:
        return NAMES.get(e.msg, e.msg)
    return "ok"


check_programs(outcome)
