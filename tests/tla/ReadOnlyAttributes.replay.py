# Replays ReadOnlyAttributes.tla: each case takes a builtin object whose type
# defines the attribute as the spec's kind, attempts the spec's steps, and
# classifies each AttributeError message as the model does.
FIELDS = ("kind", "op", "result")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SUBJECTS = {"member": (1j, "real"), "getset": (memoryview(b"a"), "nbytes"), "method": ([], "append"),
            "doc": (5, "__doc__"), "none": (5, "missing")}
MESSAGES = {"member": "readonly attribute",
            "getset": "attribute 'nbytes' of 'memoryview' objects is not writable",
            "method": "'list' object attribute 'append' is read-only",
            "doc": "'int' object attribute '__doc__' is read-only",
            "none": "'int' object has no attribute 'missing' and no __dict__ for setting new attributes"}
CATEGORIES = {"member": "readonly attribute", "getset": "not writable", "method": "read-only", "doc": "read-only",
              "none": "no __dict__"}


def snapshot(obj, name):
    try:
        return repr(getattr(obj, name))
    except AttributeError:
        return "absent"


def perform(kind, op):
    obj, name = SUBJECTS[kind]
    before = snapshot(obj, name)
    try:
        if op == "set":
            setattr(obj, name, 1)
        else:
            delattr(obj, name)
        return "ok"
    except AttributeError as e:
        if snapshot(obj, name) != before:
            return "changed"
        return CATEGORIES[kind] if str(e) == MESSAGES[kind] else "message: " + str(e)


failures = 0
count = 0
for walk in walks():
    count += 1
    steps = states(walk)
    start = next(steps)
    for state in steps:
        actual = perform(start["kind"], state["op"])
        if actual != state["result"]:
            failures += 1
            print("MISMATCH", start["kind"], "at", state["op"], "expected", state["result"], "got", actual)
            break
if failures:
    print(failures, "mismatches")
else:
    print("replayed", count, "cases")
