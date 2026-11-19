# Replays Truth.tla: each case builds the spec's classes, as plain classes,
# list subclasses or metaclasses by the holder, applies the
# spec's operation to their instances (an if over and or or among them,
# an if over or a chain of a comparison that returns the left one,
# any() or all() of a list or a generator of them, or bool() to a built-in
# value), and compares the result and the logged
# __bool__ and __len__ calls with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class Index:
    def __index__(self):
        return 2


RETURNS = {"bool_true": ("__bool__", True), "bool_false": ("__bool__", False), "bool_int": ("__bool__", 1),
           "len_zero": ("__len__", 0), "len_three": ("__len__", 3), "len_negative": ("__len__", -1),
           "len_str": ("__len__", "3"), "len_big": ("__len__", 2 ** 64), "len_index": ("__len__", Index())}


def instance(kind, side, log, holder):
    def method(name, value):
        def call(self):
            for _ in ():  # a loop: the method runs on the machine
                pass
            log.append(side + "." + name[2:-2].replace("__", ""))
            return value
        return call

    namespace = {}
    if kind.startswith("absent"):
        def absent(self):
            raise AttributeError("absent")
        namespace["__bool__"] = property(absent)
        namespace["__len__"] = method("__len__", -1 if kind == "absent_len" else 0)
    elif kind == "bool_none":
        namespace["__bool__"] = None
    elif kind == "both":
        namespace["__bool__"] = method("__bool__", False)
        namespace["__len__"] = method("__len__", 3)
    elif kind in RETURNS:
        name, value = RETURNS[kind]
        namespace[name] = method(name, value)
    if holder == "list":
        return type(kind, (list,), namespace)([0])
    if holder == "class":
        return type(kind, (type,), namespace)("C", (), {})
    return type(kind, (), namespace)()


class Less:
    def __init__(self, result):
        self.result = result

    def __lt__(self, other):
        return self.result


def tested_compare(left):
    if Less(left) < 1:
        return "then"
    return "else"


def tested_and(left, right):
    if left and right:
        return "then"
    return "else"


def tested_or(left, right):
    if left or right:
        return "then"
    return "else"


def outcome(p):
    log = []
    try:
        if "value" in p:
            return (str(bool(eval(p["value"]))), ())
        left, right = instance(p["left"], "L", log, p["holder"]), instance(p["right"], "R", log, p["holder"])
        op = p["op"]
        if op == "bool":
            result = str(bool(left))
        elif op == "not":
            result = str(not left)
        elif op == "if_compare":
            result = tested_compare(left)
        elif op == "chain":
            value = Less(left) < 1 < 2
            result = "left" if value is left else str(value)
        elif op == "if_and":
            result = tested_and(left, right)
        elif op == "if_or":
            result = tested_or(left, right)
        elif op in ("any", "all"):
            result = str((any if op == "any" else all)([left, right]))
        elif op in ("any_gen", "all_gen"):
            result = str((any if op == "any_gen" else all)(x for x in (left, right)))
        else:
            value = (left and right) if op == "and" else (left or right)
            result = "left" if value is left else "right" if value is right else repr(value)
    except Exception as error:
        result = "%s: %s" % (type(error).__name__, error)
    return (result, tuple(log))


check_programs(outcome)
