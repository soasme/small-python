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


class Names(dict):
    def __init__(self):
        super().__init__()
        self.log = []

    def __setitem__(self, key, value):
        for _ in (): pass
        if key not in ("__module__", "__qualname__", "__firstlineno__"):
            self.log.append(key)
        super().__setitem__(key, value)


class Logged(type):
    @classmethod
    def __prepare__(mcls, name, bases):
        return Names()

    def __new__(mcls, name, bases, ns):
        cls = super().__new__(mcls, name, bases, dict(ns))
        cls.log = ns.log
        return cls


def order(p):
    if p["where"] == "class":
        class C(metaclass=Logged):
            a = 1
            x: int = 2
            b = 3
        return ",".join(C.log)
    ns = Names()
    if p["where"] == "conditional":
        exec("a = 1\nif a:\n    x: int = 2\ndel a\nb: str = 3\n", {}, ns)
        return ",".join(ns.log)
    exec("a = 1\nx: int = 2\nb = 3\n", {}, ns)
    return ",".join(ns.log)


def partial(p):
    ns = {"stop": p["stop"]}
    try:
        exec("x: int = 1\nif stop: raise KeyError\ny: str = 2\n", ns)
    except KeyError:
        pass
    return render(ns["__annotate__"](1))


def calls(p):
    log = []
    def note(x):
        for _ in (): pass
        log.append(x)
        return x
    if p["owner"] == "function":
        def target(x: note(str)): pass
    elif p["owner"] == "class":
        class target:
            x: note(str)
    else:
        class Meta(type): pass
        class target(metaclass=Meta):
            x: note(str)
    if p["annotate"] == "dict":
        target.__annotate__ = lambda format: {"w": note(format)}
    elif p["annotate"] == "list":
        target.__annotate__ = lambda format: [note(format)]
    out = None
    for _ in range(2):
        try:
            out = render(target.__annotations__)
        except TypeError as error:
            out = type(error).__name__
    return "%s;%d" % (out, len(log))


PARTS = {"calls": calls, "function": function, "class": klass, "local": local, "lazy": lazy, "scope": scope, "replace": replace,
         "order": order, "partial": partial}


def outcome(p):
    try:
        return PARTS[p["part"]](p)
    except (NameError, NotImplementedError, AttributeError, TypeError) as error:
        return type(error).__name__


check_programs(outcome)
