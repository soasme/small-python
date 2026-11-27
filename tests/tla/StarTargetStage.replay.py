# Replays StarTargetStage.tla: each case compiles the module the spec
# describes and names the SyntaxError it raises by its message.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

TARGETS = {"name": "a", "alone": "*a", "two": "(*a, *b)", "call": "*f()", "valuestar": "a"}
SCOPE = "def f():\n    x = 1\n    global x\n"
NAMES = {"name 'x' is assigned to before global declaration": "scope", "'return' outside function": "return",
         "'yield' outside function": "yield", "starred assignment target must be in a list or tuple": "alone",
         "multiple starred expressions in assignment": "two", "cannot assign to function call": "call",
         "can't use starred expression here": "valuestar"}


def outcome(p):
    other = p["other"]
    source = ("return\n" if other == "before" else "") + TARGETS[p["target"]] + " = " + ("(yield)" if other == "value" else "*b" if p["target"] == "valuestar" else "1") + "\n"
    source += ("return\n" if other == "after" else "") + (SCOPE if other == "scope" else "")
    try:
        compile(source, "<stage>", "exec")
    except SyntaxError as e:
        return NAMES.get(e.msg, e.msg)
    return "ok"


check_programs(outcome)
