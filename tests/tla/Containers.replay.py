# Replays Containers.tla: each case defines the spec's class and compares
# membership, iteration, reversal, lookup, or assignment with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

ITEMS = [1, 2]


def gen(self):
    yield 1
    yield 2


class Index:
    def __init__(self, value, log):
        self.value, self.log = value, log

    def __index__(self):
        for _ in ():  # a loop: __index__ runs on the machine
            pass
        self.log.append("index")
        return self.value


def length(kind, op):
    log = []

    class X:
        def __len__(self):
            log.append("len")
            return 3 if kind == "three" else Index({"index": 2, "negative": -1, "str": "s"}[kind], log)

        def __getitem__(self, i):
            return i * 10
    try:
        x = X()
        result = repr(len(x) if op == "len" else bool(x) if op == "bool" else [y for y in reversed(x)])
    except (TypeError, ValueError) as error:
        result = type(error).__name__
    return " ".join([result] + log)


def outcome(p):
    part = p["part"]
    body = {}
    try:
        if part in ("in", "list"):
            if p["contains"] != "none":
                body["__contains__"] = (lambda r: lambda self, v: r)(1 if p["contains"] == "one" else 0)
            if p["iter"] != "none":
                body["__iter__"] = gen if p["iter"] == "gen" else None
            if p["getitem"]:
                body["__getitem__"] = lambda self, i: ITEMS[i]
            x = type("X", (), body)()
            return repr(2 in x) if part == "in" else repr(list(x))
        if part == "reversed":
            if p["rev"] != "none":
                body["__reversed__"] = (lambda self: iter([9])) if p["rev"] == "nine" else None
            if p["seq"]:
                body["__len__"] = lambda self: 2
                body["__getitem__"] = lambda self, i: ITEMS[i]
            return repr(list(reversed(type("X", (), body)())))
        if part == "missing":
            if p["missing"]:
                body["__missing__"] = lambda self, key: "m"
            d = type("D", (dict,), body)({"b": 1})
            return repr(d["a"] if p["op"] == "index" else d.get("a"))
        if part == "length":
            return length(p["length"], p["op"])
        x = type("X", (), {"__getitem__": lambda self, i: ITEMS[i]})()
        if p["op"] == "set":
            x[0] = 1
        else:
            del x[0]
        return "stored"
    except (TypeError, KeyError) as error:
        return type(error).__name__


check_programs(outcome)
