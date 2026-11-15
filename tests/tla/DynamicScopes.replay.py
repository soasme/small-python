# Replays DynamicScopes.tla: each case runs the spec's exec(), eval(), or
# locals() use and compares the result with the model's.
from harness import host

FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def exec_rebind():
    x = 1
    exec("x = 2")
    return x


def exec_new():
    exec("y = 3")
    return locals().get("y")


def exec_mapping():
    ns = {}
    exec("y = 3", globals(), ns)
    return ns


def eval_local():
    x = 1
    return eval("x + 1")


def eval_free():
    x = 1

    def inner():
        return eval("x")
    return inner()


def eval_free_referenced():
    x = 1

    def inner():
        x
        return eval("x")
    return inner()


def locals_write():
    x = 1
    d = locals()
    d["x"] = 5
    return x, locals()["x"]


def locals_snapshot():
    x = 1
    snapshot = locals()
    x = 2
    return snapshot["x"]


def frame_locals():
    x = 1
    host.frame().f_locals["x"] = 10
    return x


def eval_mappings():
    return eval("q", {"q": 2}, {"q": 3})


def class_eval():
    class C:
        a = 1
        b = eval("a + 1")
    return C.b


class Custom(dict):
    def __getitem__(self, key):
        for _ in ():  # a loop: the method runs on the machine
            pass
        if key == "q" and self.mode == "error":
            raise LookupError(key)
        if key == "q" and self.mode == "hit":
            return 3
        return dict.__getitem__(self, key)


def exec_custom(mode):
    m = Custom()
    m.mode = mode
    exec("r = q", {"q": 2}, m)
    return dict.__getitem__(m, "r")


def exec_custom_hit():
    return exec_custom("hit")


def exec_custom_miss():
    return exec_custom("miss")


def exec_custom_error():
    return exec_custom("error")


def outcome(p):
    try:
        return repr(globals()[p["case"]]())
    except (NameError, LookupError) as error:
        return type(error).__name__


check_programs(outcome)
