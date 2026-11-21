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


async def chain():
    return await Gen() + 1


class Counter:
    def __init__(self):
        self.i = 0

    def __next__(self):
        self.i += 1
        if self.i > 2:
            raise StopIteration(300)
        return self.i


class Counted:
    def __await__(self):
        return Counter()


class Bad:
    def __await__(self):
        return 5


class Wrapped:
    def __await__(self):
        return chain().__await__()  # the coroutine's wrapper


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
    target = {"coroutine": inner, "iter": Iter, "gen": Gen, "chain": chain, "bad": Bad, "next": Counted, "int": lambda: 5, "generator": generator,
              "wrapped": Wrapped}[x]

    async def main():
        return await target()
    return drive(main())


async def closing(again):
    try:
        await Gen()
    except GeneratorExit:
        if again:
            await Gen()
        return 3


async def caught_iter():
    try:
        await Iter()
    except ValueError:
        return 4


def object_program(op):
    if op == "iterthrow":
        c = caught_iter()
        c.send(None)
        try:
            c.throw(ValueError)
        except StopIteration as stop:
            return repr(stop.value)
        return "no StopIteration"
    if op in ("closed", "ignored"):
        c = closing(op == "ignored")
        c.send(None)
        try:
            return repr(c.close())
        except RuntimeError as error:
            return type(error).__name__
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


async def catching():
    try:
        await Gen()
    except ValueError:
        return 4


def wrapper_program(op):
    if op == "dropped":
        log = []

        async def held():
            try:
                await Gen()
            finally:
                log.append("closed")
        c = held()
        c.send(None)
        del c
        return " ".join(log)
    w = (chain() if op == "drive" else catching()).__await__()
    out = [next(w)]
    try:
        out.append(w.send(None) if op == "drive" else w.throw(ValueError))
    except StopIteration as stop:
        return repr(stop.value) if op == "throw" else "%r %r" % (out, stop.value)
    return "no StopIteration"


async def agen():
    try:
        yield await Gen()
    except ValueError:
        yield "caught"


def agen_program(op):
    a = agen().asend(None)
    out = [a.send(None)]
    try:
        a.send(None) if op == "send" else a.throw(ValueError)
    except StopIteration as stop:
        return "%r %r" % (out, stop.value)
    return "no StopIteration"


def outcome(p):
    if p["part"] == "agen":
        return agen_program(p["op"])
    if p["part"] == "wrapper":
        return wrapper_program(p["op"])
    return await_program(p["x"]) if p["part"] == "await" else object_program(p["op"])


check_programs(outcome)
