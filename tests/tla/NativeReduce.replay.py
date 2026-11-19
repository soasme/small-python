# Replays NativeReduce.tla: each case builds the program's class and
# instance, calls its reduction the program's way, and writes the result
# and the __getstate__ calls as the model does.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

KINDS = {"bytearray": bytearray, "set": set, "frozenset": frozenset}


def outcome(p):
    log = []
    base = KINDS[p["kind"]]
    namespace = {}
    if p["getstate"] != "none":
        def getstate(self):
            for _ in range(2): pass
            log.append("getstate")
            if p["getstate"] == "raises":
                raise ValueError("no state")
            return "S"
        namespace["__getstate__"] = getstate
    cls = type("C", (base,), namespace)
    o = cls(b"a") if base is bytearray else cls([1])
    if p["attr"]:
        o.x = 1
    name, args = ("__reduce_ex__", (p["protocol"],)) if base is bytearray else ("__reduce__", ())
    method = getattr(base, name)
    call = {"method": lambda: getattr(o, name)(*args), "type": lambda: method(o, *args),
            "map": lambda: list(map(method, [o], *[[a] for a in args]))[0]}[p["via"]]
    try:
        result = call()
    except ValueError:
        return ("ValueError", tuple(log))
    kind, items, state = result
    return ("(%s, %r, %r)" % ("C" if kind is cls else kind.__name__, (items[0] if base is bytearray else list(items[0]),) + items[1:], state),
            tuple(log))

check_programs(outcome)
