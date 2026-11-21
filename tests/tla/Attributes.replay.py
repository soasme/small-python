# Replays Attributes.tla: each case makes an object of the spec's class and
# performs the spec's steps on it, comparing every result with the model's.
FIELDS = ("kind", "getattr", "hook", "spelling", "keyed", "op", "result")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


# The name of spelling "named": every hook, error and key must be it.
class Name(str):
    pass


name = None


def given(n):
    return n is name if name is not None else type(n) is str and n == "a"


# Every value is callable, a call returning it (Call).
class Value(str):
    def __call__(self):
        return str(self)


class NonData:
    def __get__(self, obj, owner=None):
        return Value("nget")


class Data:
    def __get__(self, obj, owner=None):
        return Value("dget")

    # The instance's __dict__ past any __getattribute__ of its class.
    def __set__(self, obj, value):
        object.__getattribute__(obj, "__dict__")["a"] = value

    def __delete__(self, obj):
        object.__getattribute__(obj, "__dict__").pop("a", None)


# A key of the name's hash that is not equal to it (keyed).
class Unequal:
    def __hash__(self):
        return hash("a")

    def __eq__(self, other):
        for _ in ():
            pass
        return False


class SubProperty(property):
    pass


def refuse(self):
    raise AttributeError("refused")


def passing(self, n):
    return object.__getattribute__(self, n) if given(n) else Value("wrong name")


def supering(self, n):
    return super(type(self), self).__getattribute__(n) if given(n) else Value("wrong name")


def refusing(self, n):
    raise AttributeError(str(n) if given(n) else "wrong name")


# A __getattribute__ descriptor whose Python __get__ binds f (bound, boundrefuse).
class Bound:
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner=None):
        for _ in ():
            pass
        return lambda n: self.f(obj, n)


def make(kind, getattr, hook):
    namespace = {}
    if kind == "value":
        namespace["a"] = Value("cls")
    elif kind == "nondata":
        namespace["a"] = NonData()
    elif kind == "data":
        namespace["a"] = Data()
    elif kind == "property":
        namespace["a"] = property(lambda self: Value("pget"))
    elif kind == "raising":
        namespace["a"] = property(refuse)
    elif kind == "subproperty":
        namespace["a"] = SubProperty(lambda self: Value("pget"))
    elif kind == "subraising":
        namespace["a"] = SubProperty(refuse)
    elif kind == "slot":
        namespace["__slots__"] = ("a",)
    answer = lambda self, n: Value("ga" if given(n) else "wrong name")
    if getattr == "function":
        namespace["__getattr__"] = answer
    elif getattr == "descriptor":
        namespace["__getattr__"] = property(lambda self: lambda n: answer(self, n))
    if hook != "none":
        namespace["__getattribute__"] = {"pass": passing, "super": supering, "refuse": refusing,
                                         "bound": Bound(passing), "boundrefuse": Bound(refusing)}[hook]
    return type("C", (), namespace)()


def perform(o, op):
    try:
        if op == "get":
            return o.a if name is None else getattr(o, name)
        if op == "call":
            return o.a() if name is None else getattr(o, name)()
        if op == "del":
            if name is None:
                del o.a
            else:
                delattr(o, name)
        elif name is None:
            o.a = Value(op.split()[1])
        else:
            setattr(o, name, Value(op.split()[1]))
            # What o.__dict__ binds is the name given.
            d = object.__getattribute__(o, "__dict__") if hasattr(type(o), "__dict__") and not hasattr(type(o), "__slots__") else {}
            if "a" in d and type(type(o).__dict__.get("a")) is not Data and not any(k is name for k in d):
                return "wrong key"
        return "ok"
    except AttributeError as e:
        # getattr()'s error is named; a store's or deletion's is not.
        return "AttributeError" if name is None or op not in ("get", "call") or given(e.name) else "wrong error name"


failures = 0
count = 0
for walk in walks():
    count += 1
    steps = states(walk)
    start = next(steps)
    o = make(start["kind"], start["getattr"], start["hook"])
    if start["keyed"] and start["kind"] != "slot":
        object.__getattribute__(o, "__dict__")[Unequal()] = Value("unequal")
    name = Name("a") if start["spelling"] == "named" else None
    recent = []
    for state in steps:
        actual = perform(o, state["op"])
        recent = (recent + [state["op"]])[-8:]
        if actual != state["result"]:
            failures += 1
            print("MISMATCH", start["kind"], start["getattr"], start["hook"], start["spelling"], start["keyed"], "after", recent[:-1], "at", state["op"],
                  "expected", state["result"], "got", actual)
            break
if failures:
    print(failures, "mismatches")
else:
    print("replayed", count, "cases")
