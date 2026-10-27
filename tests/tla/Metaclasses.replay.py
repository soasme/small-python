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


def outcome(p):
    try:
        return derive(p) if p["part"] == "derive" else cell(p)
    except (TypeError, RuntimeError) as error:
        return type(error).__name__


check_programs(outcome)
