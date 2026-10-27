# Replays Tracebacks.tla: each case runs the spec's h() and walks the
# traceback of its exception, or does the explicit operation on it.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SOURCE = """def b():
    raise KeyError
def a():
    VIA
        b()
    CLAUSE
        BODY
def h():
    try:
        CALL
    except Exception as e:
        return e
"""
VIAS = {"none": ("if True:", "if False:", "pass"), "finally": ("try:", "finally:", "pass"),
        "reraise": ("try:", "except KeyError:", "raise"),
        "from": ("try:", "except KeyError as x:", "raise ValueError from x")}
CALLS = {0: "raise KeyError", 1: "b()", 2: "a()"}


def render(tb):
    out = ""
    while tb is not None:
        out += " %s:%d/%d" % (tb.tb_frame.f_code.co_name, tb.tb_lineno, tb.tb_frame.f_lineno)
        tb = tb.tb_next
    return out


def outcome(p):
    via, clause, body = VIAS[p["via"]]
    namespace = {}
    exec(SOURCE.replace("VIA", via).replace("CLAUSE", clause).replace("BODY", body).replace("CALL", CALLS[p["depth"]]),
         namespace)
    e = namespace["h"]()
    t = e.__traceback__
    TB = type(t)
    op = p["op"]
    try:
        if op == "chain":
            cause = "" if e.__cause__ is None else " cause" + render(e.__cause__.__traceback__)
            return type(e).__name__ + render(t) + cause
        if op == "construct":
            made = TB(None, t.tb_frame, 0, 5)
            return "%d %r %d" % (made.tb_lineno, made.tb_next, made.tb_lasti)
        if op == "link":
            return repr(TB(t, t.tb_frame, 1, 6).tb_next is t)
        if op == "badnext":
            TB(5, t.tb_frame, 0, 1)
        elif op == "badframe":
            TB(None, 5, 0, 1)
        elif op == "badlasti":
            TB(None, t.tb_frame, "x", 1)
        elif op == "loop":
            first = TB(None, t.tb_frame, 0, 1)
            first.tb_next = TB(first, t.tb_frame, 0, 2)
        elif op == "self":
            t.tb_next = t
        elif op == "setnext":
            t.tb_next = None
            return str(len(render(t).split()))
        elif op == "setlineno":
            t.tb_lineno = 1
        elif op == "setframe":
            t.tb_frame = None
        elif op == "setlasti":
            t.tb_lasti = 1
        elif op == "with":
            try:
                raise KeyError().with_traceback(t)
            except KeyError as raised:
                rest = raised.__traceback__
                return "%d %r" % (len(render(rest).split()), rest.tb_next is t)
        else:
            return repr(KeyError().__traceback__)
        return "no error"
    except (TypeError, ValueError, AttributeError) as error:
        return type(error).__name__


check_programs(outcome)
