# Replays BuiltinSubclasses.tla: each case defines the spec's x and class,
# makes an instance, and compares its class and value, or the exception,
# and the calls logged, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def outcome(p):
    log = []

    def note(name):
        for _ in (): pass
        log.append(name)

    raising = p["kind"] == "raise"

    class X:
        def __repr__(self):
            note("repr")
            if raising: raise KeyError
            return "X"
    if p["kind"] != "iter":
        def index(self):
            note("index")
            if raising: raise KeyError
            return 2
        X.__index__ = index
    if p["kind"] != "index":
        def iterate(self):
            note("iter")
            if raising: raise KeyError
            return iter([3, 1])
        X.__iter__ = iterate
    x = X()
    base = {"int": int, "str": str, "bytes": bytes, "tuple": tuple, "frozenset": frozenset, "bytearray": bytearray}[p["base"]]
    how = p["how"]
    if how == "meta":
        class M(type):
            def __call__(cls, *args):
                for _ in (): pass
                return super().__call__(*args)
        C = M("C", (base,), {})
    else:
        C = type("C", (base,), {})
    if how == "init":
        def init(self, *args):
            for _ in (): pass
            if args == (x,): note("init")
        C.__init__ = init
    if how == "new":
        def new(cls, *args):
            for _ in (): pass
            return super(C, cls).__new__(cls, *args)
        C.__new__ = new
    try:
        r = list(map(C, [x]))[0] if how == "map" else C(x)
    except (KeyError, TypeError) as error:
        return "%s;%s" % (type(error).__name__, ",".join(log))
    value = repr(base(r)) if base in (int, str) else repr(sorted(r) if base is frozenset else list(r))
    return "%s %s;%s" % (type(r).__name__, value, ",".join(log))


check_programs(outcome)
