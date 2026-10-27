# Replays BuiltinsScope.tla: each case evaluates a name in globals with the
# spec's __builtins__ and compares which object was found with the model's.
import builtins

FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def custom_len(value):
    return 99


def global_len(value):
    return 7


def lookup(p):
    namespace = {}
    if p["builtins"] == "module":
        namespace["__builtins__"] = builtins
    elif p["builtins"] == "custom":
        namespace["__builtins__"] = {"len": custom_len}
    elif p["builtins"] == "empty":
        namespace["__builtins__"] = {}
    if p["shadow"]:
        namespace["len"] = global_len
    name = p["name"]
    if name == "import":
        exec("import sys as found", namespace)
        return "builtin" if namespace["found"] is __import__("sys") else "other"
    builtins.added_name = "added"
    try:
        found = eval({"len": "len", "added": "added_name"}[name], namespace)
    finally:
        del builtins.added_name
    if found is global_len:
        return "global"
    if found is custom_len:
        return "custom"
    return "builtin" if found in (len, "added") else "other"


def outcome(p):
    if p["part"] == "insert":
        namespace = {}
        exec("pass", namespace)
        return repr(namespace["__builtins__"] in (builtins, builtins.__dict__))
    try:
        return lookup(p)
    except (NameError, ImportError) as error:
        return type(error).__name__


check_programs(outcome)
