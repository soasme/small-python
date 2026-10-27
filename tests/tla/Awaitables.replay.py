# Replays Awaitables.tla: each case drives a coroutine that awaits the
# spec's object, or operates on a fresh coroutine, and compares the values
# passed out and the result with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def drive(coro):
    out = []
    try:
        while True:
            out.append(coro.send(None))
    except StopIteration as stop:
        result = repr(stop.value)
    except (TypeError, RuntimeError) as error:
        result = type(error).__name__
    return "%r %s" % (out, result)


async def inner():
    return 7


class Iter:
    def __await__(self):
        return iter([1, 2])


class Gen:
    def __await__(self):
        yield 1
        return 5


class Bad:
    def __await__(self):
        return 5


def generator():
    yield 1


def awaited():
    async def main():
        c = inner()
        await c
        return await c
    return main()


def await_program(x):
    if x == "reused":
        return drive(awaited())
    target = {"coroutine": inner, "iter": Iter, "gen": Gen, "bad": Bad, "int": lambda: 5, "generator": generator}[x]

    async def main():
        return await target()
    return drive(main())


def object_program(op):
    c = inner()
    try:
        if op == "iter":
            iter(c)
        elif op == "send1":
            c.send(1)
        elif op == "close":
            c.close()
            c.send(None)
        else:
            try:
                c.throw(ValueError)
            except ValueError:
                pass
            else:
                return "no ValueError"
            try:
                c.send(None)
            except RuntimeError:
                return "ValueError RuntimeError"
        return "returned"
    except (TypeError, RuntimeError) as error:
        return type(error).__name__
    finally:
        c.close()


def outcome(p):
    return await_program(p["x"]) if p["part"] == "await" else object_program(p["op"])


check_programs(outcome)
