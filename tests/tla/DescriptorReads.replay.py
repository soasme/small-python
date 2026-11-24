# Replays DescriptorReads.tla: each case defines the spec's method on a class
# as a method or a property, reaches it on an instance by a
# builtin or a statement, and compares what happens with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def make(method, where):
    async def anext(self):
        raise StopAsyncIteration

    namespace = {"__aiter__": lambda self: self, "__anext__": anext, "__await__": lambda self: iter(()),
                 "__iter__": lambda self: iter(()), "__bool__": lambda self: False,
                 "__hash__": lambda self: 0}
    found = namespace[method]

    def read(self):
        for _ in range(2):  # a loop: the getter runs on the machine
            pass
        if where == "read":
            return found.__get__(self)
        raise (AttributeError if where == "failing" else ValueError)("read")
    if where != "class":
        namespace[method] = property(read)
    return type("C", (), namespace)()


async def statement(method, c):
    if method == "__bool__":
        if c:
            return "True"
        return "False"
    if method == "__hash__":
        {c}
    elif method == "__iter__":
        for _ in c:
            pass
    elif method == "__await__":
        await c
    else:
        async for _ in c:
            pass


def outcome(p):
    c = make(p["method"], p["where"])
    try:
        if p["via"] == "builtin":
            if p["method"] == "__bool__":
                return repr(bool(c))
            if p["method"] == "__hash__":
                hash(c)
                return "ok"
            made = aiter(c) if p["method"] == "__aiter__" else iter(c) if p["method"] == "__iter__" else anext(c)
            if p["method"] == "__anext__":
                made.close()
        else:
            try:
                statement(p["method"], c).send(None)
            except StopIteration as stop:
                if stop.value:
                    return stop.value
    except (AttributeError, TypeError, ValueError) as e:
        return "%s: %s" % (type(e).__name__, e)
    return "ok"


check_programs(outcome)
