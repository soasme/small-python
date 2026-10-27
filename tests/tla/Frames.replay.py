# Replays Frames.tla: each case takes the spec's frame and compares the
# attribute or operation's result with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SOURCE = """def caller():
    return work(1)
def work(a):
    b = a + 1
    try:
        raise KeyError
    except KeyError as e:
        fr = e.__traceback__.tb_frame
    return ACT(fr)
def gen(a):
    b = a + 1
    yield b
    yield b
"""


def act(p, namespace, fr, g):
    op = p["op"]
    try:
        if op == "f_code":
            return fr.f_code.co_name
        if op == "f_back":
            return "None" if fr.f_back is None else fr.f_back.f_code.co_name
        if op == "f_locals":
            return repr(sorted(fr.f_locals))
        if op == "f_globals":
            return "the module's" if fr.f_globals is namespace else "other"
        if op == "f_builtins":
            return "has len" if fr.f_builtins["len"] is len else "other"
        if op == "f_lasti":
            return type(fr.f_lasti).__name__
        if op == "f_generator":
            v = fr.f_generator
            return "None" if v is None else "gen" if v is g else repr(v)
        if op == "f_lineno":
            return str(fr.f_lineno)
        if op == "f_trace":
            return repr(fr.f_trace)
        if op == "settrace":
            fr.f_trace = len
            return fr.f_trace.__name__
        if op == "setlines":
            fr.f_trace_lines = False
            return repr(fr.f_trace_lines)
        if op == "setbadlines":
            fr.f_trace_lines = 1
            return "set"
        if op == "setlineno":
            fr.f_lineno = 1
            return "set"
        if op == "setcode":
            fr.f_code = None
            return "set"
        fr.clear()
        return repr(dict(fr.f_locals)) + ("" if g is None else " " + repr(g.gi_frame))
    except (TypeError, AttributeError, ValueError, RuntimeError) as error:
        return type(error).__name__


def outcome(p):
    namespace = {}
    source = p["source"]
    if source in ("running", "finished"):
        result = []
        namespace["ACT"] = (lambda fr: result.append(act(p, namespace, fr, None))) if source == "running" else (lambda fr: fr)
        exec(SOURCE, namespace)
        fr = namespace["caller"]()
        return result[0] if source == "running" else act(p, namespace, fr, None)
    exec(SOURCE, namespace)
    g = namespace["gen"](1)
    fr = g.gi_frame
    if source == "gensusp":
        next(g)
    if source == "gendone":
        list(g)
    return act(p, namespace, fr, g)


check_programs(outcome)
