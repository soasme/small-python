# Replays Reduction.tla: each case builds the program's class and instance,
# calls __reduce_ex__, and writes the result as the model does.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

BASES = {"object": object, "int": int, "list": list, "dict": dict}
NAMES = {"__newobj__": "NewObj", "__newobj_ex__": "NewObjEx", "_reconstructor": "Reconstructor"}
NEWARGS = {"args": ("__getnewargs__", lambda self: (7,)),
           "ex": ("__getnewargs_ex__", lambda self: ((7,), {})),
           "exkw": ("__getnewargs_ex__", lambda self: ((7,), {"k": 1}))}


def encode(value, cls):
    if value is cls:
        return "C"
    if type(value) is type:
        return value.__name__
    if type(value) is tuple:
        items = [encode(item, cls) for item in value]
        return "(" + ", ".join(items) + ("," if len(items) == 1 else "") + ")"
    if value is None or isinstance(value, (str, int, list, dict)):
        return repr(value)
    return repr(list(value))


def outcome(p):
    namespace = {}
    if p["slots"]:
        namespace["__slots__"] = ("s",)
    if p["getstate"]:
        namespace["__getstate__"] = lambda self: "S"
    if p["newargs"] in NEWARGS:
        name, method = NEWARGS[p["newargs"]]
        namespace[name] = method
    cls = type("C", (BASES[p["base"]],), namespace)
    o = {"object": cls, "int": lambda: cls(5), "list": lambda: cls([1]), "dict": lambda: cls(a=1)}[p["base"]]()
    if p["attr"]:
        if p["slots"]:
            o.s = 2
        else:
            o.x = 1
    try:
        result = o.__reduce_ex__(p["protocol"])
    except TypeError:
        return ("TypeError", "absent", "absent", "absent", "absent")
    items = [encode(item, cls) for item in result[1:]]
    return (NAMES[result[0].__name__], *items, *["absent"] * (4 - len(items)))


check_programs(outcome)
