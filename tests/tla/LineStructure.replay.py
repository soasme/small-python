# Replays LineStructure.tla: each case runs the spec's source and compares
# r, or the exception, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

LINES = {"comment": b"# comment", "pass": b"pass"}


def run(source):
    namespace = {}
    try:
        code = compile(source, "<program>", "exec")
    except SyntaxError:
        return None, "SyntaxError"
    try:
        exec(code, namespace)
    except TypeError:
        return None, "TypeError"
    return namespace["r"], None


def outcome(p):
    if p["kind"] == "join":
        r, error = run("r = " + "".join(p["chars"]).replace("\n", p["eol"]))
        return (error, "") if error else ("value", repr(r))
    lines = [b"# -*- coding: " + p["codec"].encode() + b" -*-" if line == "decl" else LINES[line]
             for line in (p["first"], p["second"])]
    source = (b"\xef\xbb\xbf" if p["bom"] else b"") + b"\n".join(lines) + b"\nr = '" + bytes(p["payload"]) + b"'\n"
    r, error = run(source)
    return (error, "") if error else ("value", ",".join(str(ord(c)) for c in r))


check_programs(outcome)
