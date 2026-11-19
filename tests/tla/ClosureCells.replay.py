# Replays ClosureCells.tla: each case runs a call that binds big and kept
# and makes the program's nested scope, then writes which are alive.
from harness import host

FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class Big:
    pass


SCOPES = {
    "lambda": "made = lambda: {0}",
    "def": "def made(): return {0}",
    "class": "class made:\n        x = {0}\n        def m(self): return 0",
    "genexpr": "made = ({0} for _ in 'a')",
}


def outcome(p):
    # One call per program, so that its cells are only what its scope reads.
    read = {"kept": "kept", "big": "big", "none": "0"}[p["reads"]]
    end = "raise ValueError(made, refs)" if p["ends"] == "raise" else "return made, refs"
    source = ("def call():\n    big, kept = Big(), Big()\n"
              "    refs = (host.weak_reference(big), host.weak_reference(kept))\n"
              "    " + SCOPES[p["scope"]].format(read) + "\n    " + end + "\n")
    namespace = {"Big": Big, "host": host}
    exec(source, namespace)
    try:
        made, refs = namespace["call"]()
        tb = None
    except ValueError as e:
        made, refs = e.args
        tb = e.__traceback__
    shown = ["alive" if r() is not None else "freed" for r in refs]
    result = "big %s kept %s" % tuple(shown)
    del tb, made
    return result

check_programs(outcome)
