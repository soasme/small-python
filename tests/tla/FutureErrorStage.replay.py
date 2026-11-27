# Replays FutureErrorStage.tla: each case compiles the module the spec
# describes and names the SyntaxError it raises by its message.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

FIRST = {"none": "x = 1\n", "undefined": "from __future__ import nope\n", "sameline": "x = 1; from __future__ import annotations\n",
         "laterline": "x = 1\n"}
SCOPE = "def f():\n    x = 1\n    global x\n"
NAMES = {"name 'x' is assigned to before global declaration": "scope", "future feature nope is not defined": "feature",
         "from __future__ imports must occur at the beginning of the file": "misplaced"}


def outcome(p):
    source = FIRST[p["future"]] + (SCOPE if p["scope"] == "middle" else "")
    source += "from __future__ import annotations\n" if p["future"] == "laterline" else ""
    source += SCOPE if p["scope"] == "end" else ""
    try:
        compile(source, "<stage>", "exec")
    except SyntaxError as e:
        return NAMES.get(e.msg, e.msg)
    return "ok"


check_programs(outcome)
