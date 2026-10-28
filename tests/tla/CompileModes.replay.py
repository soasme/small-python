# Replays CompileModes.tla: each case compiles the spec's source in the
# spec's mode, runs it, and compares the result and the values passed to
# the host's display hook with the model's.
from harness import host

FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SOURCES = {"expr": "1 + 1\n", "assign": "x = 1\n", "list": "x = 1; 2\n", "lines": "x = 1\ny = 2\n",
           "compound": "if 1:\n    3\n    4\n", "none": "None\n", "empty": "", "indented": " 1\n",
           "trailing": "1 + 1\n\n", "starred": "*[1], 2\n"}


def outcome(p):
    shown = []
    hook = host.display_hook()
    host.set_display_hook(shown.append)
    try:
        code = compile(SOURCES[p["source"]], "<input>", p["mode"])
        result = (eval if p["mode"] == "eval" else exec)(code, {})
        return "%r %r" % (result, shown)
    except (SyntaxError, ValueError) as error:
        return type(error).__name__
    finally:
        host.set_display_hook(hook)


check_programs(outcome)
