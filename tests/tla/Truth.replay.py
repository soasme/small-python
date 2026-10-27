# Replays Truth.tla: each case builds the spec's classes, applies the
# spec's operation to their instances (or bool() to a built-in value), and
# compares the result and the logged __bool__ and __len__ calls with the
# model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class Index:
    def __index__(self):
        return 2


RETURNS = {"bool_true": ("__bool__", True), "bool_false": ("__bool__", False), "bool_int": ("__bool__", 1),
           "len_zero": ("__len__", 0), "len_three": ("__len__", 3), "len_negative": ("__len__", -1),
           "len_str": ("__len__", "3"), "len_big": ("__len__", 2 ** 64), "len_index": ("__len__", Index())}


def instance(kind, side, log):
    def method(name, value):
        def call(self):
            log.append(side + "." + name[2:-2].replace("__", ""))
            return value
        return call

    namespace = {}
    if kind == "bool_none":
        namespace["__bool__"] = None
    elif kind == "both":
        namespace["__bool__"] = method("__bool__", False)
        namespace["__len__"] = method("__len__", 3)
    elif kind in RETURNS:
        name, value = RETURNS[kind]
        namespace[name] = method(name, value)
    return type(kind, (), namespace)()


def outcome(p):
    log = []
    try:
        if "value" in p:
            return (str(bool(eval(p["value"]))), ())
        left, right = instance(p["left"], "L", log), instance(p["right"], "R", log)
        op = p["op"]
        if op == "bool":
            result = str(bool(left))
        elif op == "not":
            result = str(not left)
        else:
            value = (left and right) if op == "and" else (left or right)
            result = "left" if value is left else "right" if value is right else repr(value)
    except Exception as error:
        result = "%s: %s" % (type(error).__name__, error)
    return (result, tuple(log))


check_programs(outcome)
