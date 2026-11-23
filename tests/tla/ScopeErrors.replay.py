# Replays ScopeErrors.tla: each case compiles the spec's declarations and
# compares the SyntaxError's message and line, or "ok", with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

OTHER = {"global": "nonlocal", "nonlocal": "global"}


def source(p):
    part = p["part"]
    if part == "decl":
        decl = p["decl"]
        prior = {"none": "pass", "param": "pass", "use": "print(x)", "assign": "x = 2", "annot": "x: int",
                 "other": OTHER[decl] + " x"}[p["prior"]]
        after = {"none": "pass", "assign": "x = 3", "annot": "x: int = 3"}[p["after"]]
        param = "x" if p["prior"] == "param" else ""
        return ("def g():\n    x = 1\n    def f(%s):\n        %s\n        %s x\n        %s\n"
                % (param, prior, decl, after))
    if part == "place":
        if p["where"] == "module":
            return "%s x\n" % p["decl"]
        return "def g():\n    x = 1\n    class C:\n        %s x\n        x = 2\n" % p["decl"]
    if part == "order":
        return {"siblings": "def f():\n    nonlocal a\ndef g():\n    nonlocal b\n",
                "inner_first": "def f():\n    def h():\n        nonlocal a\n    nonlocal b\n",
                "outer_first": "def f():\n    nonlocal b\n    def h():\n        nonlocal a\n",
                "module": "def f():\n    nonlocal a\nnonlocal top\n",
                "returns": "async def f():\n    yield 1\n    return 2\nasync def g():\n    yield 1\n    return 3\n",
                "return_first": "async def f():\n    yield 1\n    return 2\ndef g():\n    nonlocal z\n",
                "return_last": "def g():\n    nonlocal z\nasync def f():\n    yield 1\n    return 2\n"}[p["shape"]]
    if part == "statements":
        annotation, declaration = "    y: (yield)\n", "    global a\n    a: int\n"
        body = annotation + declaration if p["first"] == "annotation" else declaration + annotation
        return ("class C:\n" if p["body"] == "class" else "if 1:\n") + body
    if part == "headers":
        return {"for": "def g():\n    for x in y:\n        pass\n        global x\n",
                "except": "def g():\n    try: pass\n    except E as x:\n        global x\n",
                "case": "def g():\n    match v:\n        case [x]:\n            global x\n"}[p["header"]]
    if part == "expressions":
        a, b = "[(yield) for a in b]", "[(yield) for c in d]"
        body = {"assign": "x[A] = (\n        B)", "for": "for x[A] in (\n        B): pass",
                "annassign": "x[A]: int = (\n        B)", "dict": "{1: A, (\n        B): 2}",
                "call": "f(k=A, *(\n        B))", "decorator": "@A\n    def f(a=B): pass",
                "dictcomp": "{A: (\n        B) for z in w}", "cond": "(A if (\n        B) else 1)"}[p["shape"]]
        return "def g():\n    " + body.replace("A", a).replace("B", b) + "\n"
    if part == "locals":
        return "def g():\n    " + {"assign": "x = (y := 1)", "for": "for x in (y := []): pass",
                                     "annassign": "x: int = (y := 1)", "def": "def f(a=(z := 1)): pass",
                                     "annotated": "x: int\n    y = 1\n    x = 2", "unused": "x: int\n    y = 1"}[p["shape"]] + "\n"
    binding = {"enclosing": "def g():\n    x = 1\n", "module": "x = 1\ndef g():\n", "none": "def g():\n"}[p["source"]]
    return binding + "    def f():\n        nonlocal x\n"


def outcome(p):
    try:
        code = compile(source(p), "<scope>", "exec")
        if p["part"] == "locals":
            namespace = {}
            exec(code, namespace)
            return ",".join(namespace["g"].__code__.co_varnames)
        return "ok"
    except SyntaxError as error:
        return "%s@%s" % (error.msg, error.lineno)


check_programs(outcome)
