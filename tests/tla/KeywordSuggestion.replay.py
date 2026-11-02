# Replays KeywordSuggestion.tla: each case calls a function with the
# program's parameters by the program's keyword and reads the suggestion.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def outcome(p):
    params = ["".join(word) for word in p["params"]]
    name = "".join(p["name"])
    namespace = {}
    exec("def f(" + "".join(f"{c}=None, " for c in params) + "): pass", namespace)
    try:
        namespace["f"](**{name: 1})
    except TypeError as error:
        text = str(error)
        marker = ". Did you mean '"
        if marker not in text:
            return ("TypeError", "-")
        return ("TypeError", tuple(text[text.index(marker) + len(marker):-2]))
    return ("bound", "-")


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
