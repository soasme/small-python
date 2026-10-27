# Replays ScopeErrors.tla: each case compiles the spec's declarations and
# compares the SyntaxError's message and line, or "ok", with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

OTHER = {"global": "nonlocal", "nonlocal": "global"}


def source(p):
    part = p["part"]
    if part == "decl":
        decl = p["decl"]
        prior = {"none": "pass", "param": "pass", "use": "print(x)", "assign": "x = 2", "annot": "x: int",
                 "other": OTHER[decl] + " x"}[p["prior"]]
        after = {"none": "pass", "assign": "x = 3", "annot": "x: int = 3"}[p["after"]]
        param = "x" if p["prior"] == "param" else ""
        return ("def g():\n    x = 1\n    def f(%s):\n        %s\n        %s x\n        %s\n"
                % (param, prior, decl, after))
    if part == "place":
        if p["where"] == "module":
            return "%s x\n" % p["decl"]
        return "def g():\n    x = 1\n    class C:\n        %s x\n        x = 2\n" % p["decl"]
    binding = {"enclosing": "def g():\n    x = 1\n", "module": "x = 1\ndef g():\n", "none": "def g():\n"}[p["source"]]
    return binding + "    def f():\n        nonlocal x\n"


def outcome(p):
    try:
        compile(source(p), "<scope>", "exec")
        return "ok"
    except SyntaxError as error:
        return "%s@%s" % (error.msg, error.lineno)


check_programs(outcome)
