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


class Logging(dict):
    def __setitem__(self, key, value):
        for _ in ():  # a loop: the method runs on the machine
            pass
        self.log.append(("set", key, value))
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        for _ in ():
            pass
        self.log.append(("del", key))
        dict.__delitem__(self, key)


def exec_custom_loop():
    m = Logging()
    m.log = []
    exec("for i in (1, 2): pass\nfor i in (x for x in (3,)): pass\nk = j = 0\ndel k, j", {}, m)
    return m.log


class Hiding(dict):
    def __getitem__(self, key):
        self.log.append(key)
        if key == "z":
            raise KeyError(key)
        return dict.__getitem__(self, key)


def exec_globals_storage():
    g = Hiding(q=2, z=4)
    g.log = []
    exec("r = (q, z, len('ab'))\nclass C:\n    w = q\ns = C.w\ndef f(): return q\nt = f()", g)
    return tuple(dict.__getitem__(g, k) for k in "rst") + (g.log,)


class Key:
    def __init__(self, log):
        self.log = log

    def __hash__(self):
        return hash("v")

    def __eq__(self, other):
        for _ in ():  # a loop: the method runs on the machine
            pass
        self.log.append(other)
        return other == "v"


def eval_key_eq():
    log = []
    return eval("v", {Key(log): 5}), log


class Marking(dict):
    def __getitem__(self, key):
        for _ in ():  # a loop: the method runs on the machine
            pass
        Marking.log.append(key)
        return dict.__getitem__(self, key)


class Meta(type):
    @classmethod
    def __prepare__(mcls, name, bases):
        return Marking()


def class_annotation_future():
    Marking.log = []
    exec("from __future__ import annotations\nclass E(metaclass=Meta):\n    x: int = 1\n", {"Meta": Meta})
    return Marking.log


def outcome(p):
    try:
        return repr(globals()[p["case"]]())
    except (NameError, LookupError) as error:
        return type(error).__name__


check_programs(outcome)
