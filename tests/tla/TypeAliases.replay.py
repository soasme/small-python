# Replays TypeAliases.tla: each case runs the spec's type statement in a
# fresh __main__ namespace and compares what it reads, and how often the
# value was evaluated, with the model's result.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

VALUES = {"int": "log(int)", "later": "log(Later)", "never": "log(Never)", "self": "log(list[A])"}
QUERIES = {"value": "A.__value__", "value2": "(A.__value__, A.__value__)[1]", "name": "A.__name__",
           "module": "A.__module__", "params": "A.__type_params__", "subscript": "A[str]",
           "type": "type(A).__name__", "set": "setattr(A, '__value__', 1)"}


def text(value):
    if isinstance(value, type):
        return value.__name__
    if isinstance(value, str):
        return value
    return repr(value).replace("__main__.", "")


def outcome(p):
    log = []
    namespace = {"__name__": "__main__", "log": lambda v: (log.append(1), v)[1]}
    source = "type A%s = %s\nLater = int\nresult = %s" % ("[K]" if p["generic"] else "", VALUES[p["value"]],
                                                          QUERIES[p["query"]])
    try:
        exec(source, namespace)
    except (NameError, TypeError, AttributeError) as error:
        return type(error).__name__
    return "%s %d" % (text(namespace["result"]), len(log))


check_programs(outcome)
