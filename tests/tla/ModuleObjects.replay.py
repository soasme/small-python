# Replays ModuleObjects.tla: each case makes a module with the module type
# and compares what the operation reads, or the exception, with the
# model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

import builtins

OPS = {"set": "m.x = 1\nr = m.__dict__['x']", "dictset": "m.__dict__['y'] = 2\nr = m.y",
       "del": "m.x = 1\ndel m.x\nr = hasattr(m, 'x')", "delmiss": "del m.nope", "getmiss": "m.nope",
       "setdict": "m.__dict__ = {}", "global": "exec('__dict__', m.__dict__)",
       "annotate": "exec('a: int = 1', m.__dict__)\nr = m.__annotations__", "rename": "m.__name__ = 'r'\nr = m.__name__"}


def outcome(p):
    module_type = type(builtins)
    m = module_type("m", "doc") if p["doc"] else module_type("m")
    namespace = {"m": m}
    try:
        if p["op"] == "read":
            return repr(getattr(m, p["attr"]))
        exec(OPS[p["op"]], namespace)
    except (AttributeError, NameError) as error:
        return type(error).__name__
    return repr(namespace.get("r"))


check_programs(outcome)
