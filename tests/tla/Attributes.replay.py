# Replays Attributes.tla: each case makes an object of the spec's class and
# performs the spec's steps on it, comparing every result with the model's.
FIELDS = ("kind", "getattr", "hook", "op", "result")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class NonData:
    def __get__(self, obj, owner=None):
        return "nget"


class Data:
    def __get__(self, obj, owner=None):
        return "dget"

    # The instance's __dict__ past any __getattribute__ of its class.
    def __set__(self, obj, value):
        object.__getattribute__(obj, "__dict__")["a"] = value

    def __delete__(self, obj):
        object.__getattribute__(obj, "__dict__").pop("a", None)


def refuse(self):
    raise AttributeError("refused")


def passing(self, name):
    return object.__getattribute__(self, name)


def refusing(self, name):
    raise AttributeError(str(name))


def make(kind, getattr, hook):
    namespace = {}
    if kind == "value":
        namespace["a"] = "cls"
    elif kind == "nondata":
        namespace["a"] = NonData()
    elif kind == "data":
        namespace["a"] = Data()
    elif kind == "property":
        namespace["a"] = property(lambda self: "pget")
    elif kind == "raising":
        namespace["a"] = property(refuse)
    elif kind == "slot":
        namespace["__slots__"] = ("a",)
    if getattr:
        namespace["__getattr__"] = lambda self, name: str("ga")
    if hook != "none":
        namespace["__getattribute__"] = passing if hook == "pass" else refusing
    return type("C", (), namespace)()


def perform(o, op):
    try:
        if op == "get":
            return o.a
        if op == "del":
            del o.a
        else:
            o.a = op.split()[1]
        return "ok"
    except AttributeError:
        return "AttributeError"


failures = 0
count = 0
for walk in walks():
    count += 1
    steps = states(walk)
    start = next(steps)
    o = make(start["kind"], start["getattr"], start["hook"])
    recent = []
    for state in steps:
        actual = perform(o, state["op"])
        recent = (recent + [state["op"]])[-8:]
        if actual != state["result"]:
            failures += 1
            print("MISMATCH", start["kind"], start["getattr"], start["hook"], "after", recent[:-1], "at", state["op"],
                  "expected", state["result"], "got", actual)
            break
if failures:
    print(failures, "mismatches")
else:
    print("replayed", count, "cases")
