# Replays CodeObjects.tla: each case defines the spec's function f and
# compares the code attribute or operation's result with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

MASK = 0x4 | 0x8 | 0x10 | 0x20 | 0x80 | 0x200 | 0x4000000


def source(p):
    kind = p["kind"]
    value = "(len.__name__, v)" if p["closure"] == "free" else "len.__name__"
    body = ['"doc"'] if p["doc"] else []
    if p["closure"] == "cell":
        body += ["x = 1", "g = lambda: x"]
    body.append(("yield " if kind in ("gen", "asyncgen") else "return ") + value)
    head = ("async def" if kind in ("async", "asyncgen") else "def") + " f(" + p["sig"]["text"] + "):"
    lines = [head] + ["    " + line for line in body]
    if p["nested"]:
        lines = ["def outer():", "    v = 1"] + ["    " + line for line in lines] + ["    return f", "f = outer()"]
    return "\n".join(["v = 1"] + lines) + "\n"


def outcome(p):
    namespace = {}
    exec(source(p), namespace)
    co = namespace["f"].__code__
    op = p["op"]
    try:
        if op == "read":
            v = getattr(co, p["attr"])
            if p["attr"] == "co_names":
                return repr(tuple(sorted(v)))
            if p["attr"] == "co_flags":
                return str(v & MASK)
            return repr(v)
        if op == "doc":
            return repr(co.co_consts[0]) if co.co_flags & 0x4000000 else "no docstring"
        if op == "replace":
            r = co.replace(co_name="z", co_firstlineno=9)
            return " ".join([r.co_name, str(r.co_firstlineno), co.co_name, str(r == co)])
        if op == "copy":
            r, same = co.replace(), co.replace(co_name=co.co_name, co_argcount=co.co_argcount, co_varnames=co.co_varnames)
            return str(r == co and hash(r) == hash(co) and same == co and hash(same) == hash(co))
        if op in ("rename", "resig"):
            f, sig = namespace["f"], p["sig"]
            count = len(sig["names"]) + sig["varargs"] + sig["kwargs"]
            if op == "rename":
                renamed = tuple("n_" + n for n in co.co_varnames[:count]) + co.co_varnames[count:]
                f.__code__ = co.replace(co_varnames=renamed)
                calls = [((0,) * sig["argc"], {"n_" + n: 0 for n in sig["names"][sig["argc"]:]}),
                         ((0,) * sig["argc"], {n: 0 for n in sig["names"][sig["argc"]:]})]
            else:
                f.__code__ = co.replace(co_argcount=0, co_posonlyargcount=0, co_kwonlyargcount=len(sig["names"]))
                calls = [((), {n: 0 for n in sig["names"]}), ((0,) * len(sig["names"]), {})]
            results = []
            for args, kwargs in calls:
                try:
                    result = f(*args, **kwargs)
                    if hasattr(result, "close"):
                        result.close()
                    results.append("ok")
                except TypeError as error:
                    results.append(type(error).__name__)
            return " ".join(results)
        if op == "setattr":
            co.co_name = "x"
            return "set"
        if op == "badkw":
            co.replace(nope=1)
            return "replaced"
        if op == "lines":
            ranges = list(co.co_lines())
            ok = all(len(t) == 3 and t[1] >= t[0] for t in ranges) and \
                all(a[1] == b[0] for a, b in zip(ranges, ranges[1:])) and \
                (not ranges or (ranges[0][0] == 0 and ranges[-1][1] == len(co.co_code)))
            return "ok" if ok else repr(ranges)
        positions = list(co.co_positions())
        return "ok" if all(len(t) == 4 for t in positions) else repr(positions)
    except (TypeError, AttributeError) as error:
        return type(error).__name__


check_programs(outcome)
