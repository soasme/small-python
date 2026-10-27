# Replays Generics.tla: each case defines the spec's generic function,
# class, or alias and compares what it reads with the model's result.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

PARAMS = {"plain": "T", "bound": "T: int", "constraints": "T: (str, bytes)", "default": "T = int",
          "tuple": "*T", "spec": "**T"}
DEFINITIONS = {"function": "def g[%s](): pass\nresult = g", "class": "class g[%s]: pass\nresult = g",
               "alias": "type g[%s] = int\nresult = g"}


def text(value):
    if isinstance(value, type):
        return value.__name__
    if isinstance(value, tuple):
        return "(%s)" % ", ".join(text(v) for v in value) if len(value) != 1 else "(%s,)" % text(value[0])
    return repr(value).replace("typing.", "").replace("__main__.", "")


def run(source):
    namespace = {}
    exec(source, namespace)
    return namespace["result"]


def param(p):
    t = run(DEFINITIONS[p["kind"]] % PARAMS[p["param"]]).__type_params__[0]
    query = p["query"]
    if query == "type":
        return type(t).__name__
    return text(getattr(t, {"bound": "__bound__", "constraints": "__constraints__", "default": "__default__",
                            "infer": "__infer_variance__"}[query]))


def visible(p):
    where = p["where"]
    if where == "annotation":
        return text(run("def g[T](x: T): pass\nresult = g.__annotations__['x']"))
    if where == "body":
        return text(run("def g[T](): return T\nresult = g()"))
    if where == "method":
        return text(run("class g[T]:\n    def m(self): return T\nresult = g().m()"))
    if where == "shadow":
        return text(run("class g[T]:\n    T = 5\n    x: T\nresult = g.__annotations__['x']"))
    return text(run("def g[T](): pass\nresult = T"))


def syntax(p):
    source = {"duplicate": "def g[T, T](): pass", "order": "def g[T = int, U](): pass", "ok": "def g[T, U = int](): pass"}
    compile(source[p["case"]], "<generic>", "exec")
    return "ok"


def klass(p):
    query = p["query"]
    C = run("class C[T]: pass\nresult = C")
    if query == "bases":
        return text(C.__bases__)
    if query == "orig":
        return "(%s,)" % text(C.__orig_bases__[0])
    return text(C[int])


PARTS = {"param": param, "visible": visible, "syntax": syntax, "class": klass}


def outcome(p):
    try:
        if p["part"] == "lazy":
            declared = {"bound": "T: X", "constraints": "T: (X, X)", "default": "T = X"}[p["what"]]
            attribute = {"bound": "__bound__", "constraints": "__constraints__", "default": "__default__"}[p["what"]]
            bind = "X = int\n" if p["defined"] else ""
            return text(run("def g[%s](): pass\n%sresult = g.__type_params__[0].%s" % (declared, bind, attribute)))
        return PARTS[p["part"]](p)
    except (NameError, SyntaxError, AttributeError) as error:
        return type(error).__name__


check_programs(outcome)
