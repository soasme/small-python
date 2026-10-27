# Replays FunctionObjects.tla: each case defines the spec's function f,
# reads or writes the attribute, and compares the repr of what is read or
# returned, or the exception, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

PARAMS = {"plain": ("(x)", "x"), "default": ("(x=1)", "x"), "kwonly": ("(*, x=1)", "x"),
          "both": ("(x=1, *, y=2)", "(x, y)"), "generic": ("[T](x)", "x")}


def define(p):
    params, result = PARAMS[p["params"]]
    head = "def f" + params + (" -> int" if p["annotated"] else "") + ":\n"
    body = ("    'doc'\n" if p["doc"] else "") + ("    v\n" if p["place"] == "nested" else "") + "    return " + result + "\n"
    if p["place"] == "module":
        return head + body
    if p["place"] == "class":
        return "class C:\n" + "".join("    " + line + "\n" for line in (head + body).splitlines()) + "f = C.f\n"
    return ("def g():\n    v = 5\n" + "".join("    " + line + "\n" for line in (head + body).splitlines()) +
            "    return f\nf = g()\n")


def show(namespace, f, attr):
    if attr == "call":
        return repr(f())
    value = getattr(f, attr)
    if attr == "__closure__":
        return "None" if value is None else "cells " + " ".join(repr(c.cell_contents) for c in value)
    if attr == "__annotate__":
        return "None" if value is None else "function" if callable(value) else repr(value)
    if attr == "__globals__":
        return "the module's globals" if value is namespace else repr(type(value))
    if attr == "__builtins__":
        return type(value).__name__
    return repr(value)


def outcome(p):
    namespace = {"__name__": "m"}
    exec(define(p), namespace)
    f = namespace["f"]
    try:
        if p["op"] == "read":
            return show(namespace, f, p["attr"])
        exec("f." + p["attr"], {"f": f})
        name = p["attr"].split(" = ")[0]
        if name in ("__defaults__", "__kwdefaults__", "__code__"):
            return repr(f())
        if name == "__dict__":
            return repr(f.y)
        if name == "x":
            return repr(f.__dict__)
        return repr(getattr(f, name))
    except (TypeError, AttributeError, ValueError) as error:
        return type(error).__name__


check_programs(outcome)
