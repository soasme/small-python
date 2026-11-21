# Replays Metaclasses.tla: each case runs a class statement with the spec's
# bases and metaclass and compares the metaclass chosen with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class MA(type):
    pass


class MB(MA):
    pass


class MC(type):
    pass


class A(metaclass=MA):
    pass


class B(metaclass=MB):
    pass


class C(metaclass=MC):
    pass


class Entries:
    def __mro_entries__(self, bases):
        return (B,)


E = Entries()


def func(name, bases, namespace):
    return "f"


BASES = {"none": (), "A": (A,), "B": (B,), "C": (C,), "AB": (A, B), "AC": (A, C), "E": (E,), "EA": (E, A)}
METAS = {"type": type, "MA": MA, "MB": MB, "MC": MC, "func": func}


def derive(p):
    bases = BASES[p["bases"]]
    if p["meta"] == "none":
        class X(*bases):
            pass
    else:
        class X(*bases, metaclass=METAS[p["meta"]]):
            pass
    if X == "f":
        return "f"
    return type(X).__name__ + (" orig" if "__orig_bases__" in X.__dict__ else " plain")


def cell(p):
    class Meta(type):
        def __new__(meta, name, bases, namespace):
            if p["cell"] == "dropped":
                namespace = {k: v for k, v in namespace.items() if k != "__classcell__"}
            return super().__new__(meta, name, bases, namespace)
    if p["cell"] == "unused":
        class X(metaclass=Meta):
            def get(self):
                return type(self)
    else:
        class X(metaclass=Meta):
            def get(self):
                return __class__
    return X().get().__name__


def called(p):
    log = []

    def made(name, bases, namespace, **kw):
        for _ in (): pass
        log.append("%s flag %s" % (name, kw["flag"]))
        if p["made"] == "raises":
            raise KeyError(name)
        return "f" if p["made"] == "marker" else type(name, bases, namespace)

    class X(metaclass=made, flag=1):
        def get(self):
            return __class__
    return " ".join([X if X == "f" else X().get().__name__] + log)


def built(p):
    log = []

    def builder(func, name, *bases, **kw):
        for _ in (): pass
        log.append("build %s %s" % (name, " ".join(sorted(kw))))
        if p["made"] == "raises":
            raise KeyError(name)
        return "f" if p["made"] == "marker" else __build_class__(func, name, *bases)

    body = "    for i in range(2): pass\n" if p["loops"] else "    x = 1\n"
    namespace = {"__name__": "replay", "__builtins__": dict(vars(__build_class__.__self__), __build_class__=builder)}
    exec("class X(flag=1):\n" + body, namespace)
    X = namespace["X"]
    return " ".join([X if X == "f" else X.__name__] + log)


def delegated(p):
    log = []

    class MD(type):
        def __new__(meta, name, bases, namespace):
            for _ in (): pass
            log.append("new")
            if p["raises"]:
                raise KeyError(name)
            return super().__new__(meta, name, bases, namespace)

        def __init__(cls, name, bases, namespace):
            log.append("init")

    D = type.__new__(MD, "D", (), {})
    del log[:]
    X = type("X", (D,), {}) if p["via"] == "type" else type.__new__(type, "X", (D,), {})
    return " ".join([type(X).__name__] + log)


def entries(p):
    log = []

    class G:
        def __getattr__(self, name):
            for _ in (): pass
            log.append(name)
            if p["hook"] == "found":
                return lambda bases: ()
            raise (AttributeError if p["hook"] == "missing" else KeyError)(name)

    try:
        type("X", (G(),), {}) if p["via"] == "type" else type.__new__(type, "X", (G(),), {})
    except TypeError as error:
        return ("entries" if "MRO entry" in str(error) else "conflict" if "metaclass conflict" in str(error) else "other") + " %d" % len(log)
    except KeyError:
        return "KeyError %d" % len(log)
    return "made"


def outcome(p):
    try:
        if p["part"] == "entries":
            return entries(p)
        if p["part"] == "delegate":
            return delegated(p)
        if p["part"] == "builder":
            return built(p)
        if p["part"] == "call":
            return called(p)
        return derive(p) if p["part"] == "derive" else cell(p)
    except (TypeError, RuntimeError, KeyError) as error:
        return type(error).__name__


check_programs(outcome)
