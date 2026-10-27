# Replays Identifiers.tla: each case assigns to the spec's name and
# compares the name bound, or the exception, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

CHARS = {"e-acute": "é", "a-acute": "á", "middot": "·", "euro": "€", "fraktur-H": "ℌ",
         "roman-9": "Ⅸ", "acute": "́", "fi": "ﬁ", "fw-i": "ｉ", "fw-f": "ｆ", "fw-g": "ｇ",
         "fw-T": "Ｔ", "sup2": "²"}
NAMES = {char: name for name, char in CHARS.items()}


def outcome(p):
    namespace = {}
    try:
        code = compile("".join(CHARS.get(c, c) for c in p) + " = 1", "<program>", "exec")
        exec(code, namespace)
    except (SyntaxError, ValueError) as error:
        return (type(error).__name__, "")
    (name,) = [key for key in namespace if key != "__builtins__"]
    return ("ok", ".".join(NAMES.get(c, c) for c in name))


check_programs(outcome)
