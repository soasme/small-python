# Replays Singletons.tla: each case runs the spec's operation on the
# spec's expressions and compares the result's repr, or the exception,
# with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SOURCES = {"is": "r = ({x}) is ({y})", "bool": "r = bool({x})", "not": "r = not {x}", "repr": "r = repr({x})",
           "sub": "class C(type({x})): pass\nr = C", "attr": "({x}).a = 1\nr = None"}


def f():
    pass


def outcome(p):
    namespace = {"f": f}
    try:
        exec(SOURCES[p["op"]].format(x=p["x"], y=p.get("y")), namespace)
    except (TypeError, AttributeError) as error:
        return type(error).__name__
    r = namespace["r"]
    return r if type(r) is str else repr(r)


check_programs(outcome)
