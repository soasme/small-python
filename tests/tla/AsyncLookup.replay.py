# Replays AsyncLookup.tla: each case defines the spec's method on a class
# as a method or a failing property, reaches it on an instance by a
# builtin or a statement, and compares what happens with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def make(method, where):
    def read(self):
        raise (AttributeError if where == "failing" else ValueError)("read")

    async def anext(self):
        raise StopAsyncIteration

    namespace = {"__aiter__": lambda self: self, "__anext__": anext, "__await__": lambda self: iter(())}
    if where != "class":
        namespace[method] = property(read)
    return type("C", (), namespace)()


async def statement(method, c):
    if method == "__await__":
        await c
    else:
        async for _ in c:
            pass


def outcome(p):
    c = make(p["method"], p["where"])
    try:
        if p["via"] == "builtin":
            made = aiter(c) if p["method"] == "__aiter__" else anext(c)
            if p["method"] == "__anext__":
                made.close()
        else:
            try:
                statement(p["method"], c).send(None)
            except StopIteration:
                pass
    except (AttributeError, ValueError) as e:
        return "%s: %s" % (type(e).__name__, e)
    return "ok"


check_programs(outcome)
