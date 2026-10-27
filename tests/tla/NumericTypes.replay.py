# Replays NumericTypes.tla: each case evaluates the spec's expression and
# compares the result's type and repr (a str result as itself), or the
# exception, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

UNARY = {"~": "~({x})", "neg": "-({x})", "str": "str({x})", "repr": "repr({x})"}
COMPLEX = {"real": "z.real", "imag": "z.imag", "set real": "setattr(z, 'real', 0.0)", "set imag": "setattr(z, 'imag', 0.0)"}


def spell(v):
    kind, n = v
    return ("False", "True")[n] if kind == "bool" else str(n)


def outcome(p):
    kind = p["kind"]
    if kind == "binary":
        source = "({}) {} ({})".format(spell(p["x"]), p["op"], spell(p["y"]))
    elif kind == "unary":
        source = UNARY[p["op"]].format(x=spell(p["x"]))
    elif kind == "literal":
        source = "".join(p["text"])
    else:
        source = COMPLEX[p["op"]]
    try:
        r = eval(compile(source, "<program>", "eval"), {"z": 1.5 + 2j})
    except (SyntaxError, ValueError, AttributeError) as error:
        return (type(error).__name__, "")
    return (type(r).__name__, r if type(r) is str else repr(r))


check_programs(outcome)
