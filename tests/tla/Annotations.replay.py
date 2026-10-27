# Replays Annotations.tla: each case defines the spec's annotated function,
# class, or local and compares the annotations, value, or exception with
# the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def render(annotations):
    return ",".join("%s=%s" % (k, v.__name__ if isinstance(v, type) else repr(v))
                    for k, v in annotations.items() if k != "return")


def function(p):
    ann = p["ann"]
    if ann == "string":
        def f(x: "T"): pass
    elif ann == "later":
        def f(x: T): pass
    else:
        def f(x: Never): pass
    T = str
    if p["op"] == "annotations":
        return render(f.__annotations__)
    return render(f.__annotate__(1 if p["op"] == "format1" else 3))


def klass(p):
    ann, value = p["ann"], p["value"]
    if ann == "string" and value:
        class C:
            x: "T" = 1
    elif ann == "string":
        class C:
            x: "T"
    elif ann == "later" and value:
        class C:
            x: T = 1
    elif ann == "later":
        class C:
            x: T
    elif value:
        class C:
            x: Never = 1
    else:
        class C:
            x: Never
    T = str
    if p["op"] == "attr":
        return repr(C.x)
    return render(C.__annotations__)


def local(p):
    if p["value"]:
        def f():
            x: Never = 1
            return x
    else:
        def f():
            x: Never
            return x
    return repr(f())


def lazy(p):
    log = []
    def side():
        log.append(1)
        return int
    class C:
        x: side()
    for _ in range(p["reads"]):
        C.__annotations__
    return repr(len(log))


def scope(p):
    if p["where"] == "class":
        class C:
            U = int
            x: U
        return render(C.__annotations__)
    def outer():
        q = float
        def inner(x: q): pass
        return inner
    return render(outer().__annotations__)


def replace(p):
    if p["target"] == "function":
        def target(x: int): pass
    else:
        class target:
            x: int
    op = p["op"]
    if op == "annotations":
        target.__annotations__ = {"z": 1}
        return repr(target.__annotate__)
    if op == "annotate":
        target.__annotate__ = lambda format: {"w": 2}
        return render(target.__annotations__)
    if op == "bad":
        target.__annotate__ = 5
    else:
        del target.__annotate__
    return "kept"


PARTS = {"function": function, "class": klass, "local": local, "lazy": lazy, "scope": scope, "replace": replace}


def outcome(p):
    try:
        return PARTS[p["part"]](p)
    except (NameError, NotImplementedError, AttributeError, TypeError) as error:
        return type(error).__name__


check_programs(outcome)
