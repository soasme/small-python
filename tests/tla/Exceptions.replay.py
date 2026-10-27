# Replays Exceptions.tla: each case writes out the spec's program as Python
# source, runs it, and compares the blocks it ran and how it ended with the
# model's. Uses only the core language.
FIELDS = ("program", "log", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class E1(Exception):
    pass


class E2(Exception):
    pass


class CM:
    def __init__(self, log, exit):
        self.log, self.exit = log, exit

    def __enter__(self):
        self.log.append("enter")

    def __exit__(self, kind, value, traceback):
        self.log.append("exit:" + (kind.__name__ if kind else "None"))
        if self.exit == "E2":
            raise E2()
        return self.exit == "suppress"


ACTIONS = {"pass": "", "E1": "raise E1()", "E2": "raise E2()", "reraise": "raise",
           "return": "return {name!r}", "break": "break", "continue": "continue"}


def block(name, action, indent):
    lines = [f"log.append({name!r})"]
    if ACTIONS[action]:
        lines.append(ACTIONS[action].format(name=name))
    return "".join(" " * indent + line + "\n" for line in lines)


def source(program):
    if program["shape"] == "try":
        statement = ("        try:\n" + block("body", program["body"], 12) +
                     "        except E1:\n" + block("handler", program["handler"], 12) +
                     "        else:\n" + block("else", program["else"], 12) +
                     "        finally:\n" + block("finally", program["finally"], 12))
    else:
        statement = f"        with CM(log, {program['exit']!r}):\n" + block("body", program["body"], 12)
    return "def run():\n    for _ in range(1):\n" + statement + "        log.append('after')\n    return 'end'\n"


def outcome(run):
    try:
        return ("return", run(), ())
    except BaseException as error:
        chain = []
        while error is not None:
            chain.append(type(error).__name__)
            error = error.__context__
        return ("raise", "", tuple(chain))


failures = 0
count = 0
for walk in walks():
    count += 1
    steps = states(walk)
    program = next(steps)["program"]
    for state in steps:
        namespace = {"log": [], "E1": E1, "E2": E2, "CM": CM}
        exec(compile(source(program), "<program>", "exec"), namespace)
        ended = outcome(namespace["run"])
        actual = (tuple(namespace["log"]), ended)
        if actual != (state["log"], state["outcome"]):
            failures += 1
            if failures <= 20:
                print("MISMATCH", program, "expected", (state["log"], state["outcome"]), "got", actual)
if failures:
    print(failures, "mismatches")
else:
    print("replayed", count, "cases")
