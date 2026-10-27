# Replays AsyncFor.tla: each case drives a coroutine running async for over
# the spec's source, or an asynchronous comprehension, or compiles one in a
# plain function, and compares the values passed out and the items with the
# model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def drive(coro):
    out = []
    try:
        while True:
            out.append(coro.send(None))
    except StopIteration as stop:
        result = repr(stop.value)
    except (TypeError, KeyError) as error:
        result = type(error).__name__
    return "%r %s" % (out, result)


class Step:
    def __await__(self):
        yield "tick"


async def agen():
    for i in range(2):
        await Step()
        yield i


class Counter:
    def __init__(self):
        self.i = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        self.i += 1
        if self.i > 2:
            raise StopAsyncIteration
        return self.i


class NoAiter:
    pass


class BadAnext:
    def __aiter__(self):
        return self

    def __anext__(self):
        return 5


class NoAnext:
    def __aiter__(self):
        return 5


SOURCES = {"agen": agen, "class": Counter, "noaiter": NoAiter, "badanext": BadAnext, "noanext": NoAnext}
SYNTAX = {"for": "def f():\n    async for x in y: pass", "with": "def f():\n    async with x: pass",
          "await": "def f():\n    await x", "comprehension": "def f():\n    return [x async for x in y]"}


def loop(source, body):
    async def main():
        items = []
        async for x in source():
            items.append(x)
            if body == "break":
                break
            if body == "raise":
                raise KeyError
        else:
            items.append("else")
        return items
    return drive(main())


def comprehension(kind):
    async def main():
        if kind == "list":
            return [x async for x in agen()]
        if kind == "set":
            return {x async for x in agen()}
        return {x: x async for x in agen()}
    return drive(main())


def outcome(p):
    part = p["part"]
    if part == "loop":
        return loop(SOURCES[p["source"]], p["body"])
    if part == "comprehension":
        return comprehension(p["kind"])
    try:
        compile(SYNTAX[p["construct"]], "<async>", "exec")
        return "compiled"
    except SyntaxError as error:
        return type(error).__name__


check_programs(outcome)
