# Replays AnextDefault.tla: each case suspends a coroutine in an await of
# anext(it, "d"), it's __anext__ coroutine, or it an async generator,
# suspended in an await of its own, resumes the coroutine as the program
# says, and writes what that did.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class Pause:
    def __await__(self):
        return (yield "p")


def outcome(p):
    class It:
        def __aiter__(self):
            return self

        async def __anext__(self):
            try:
                got = await Pause()
            except KeyError:
                if p["after"] == "return":
                    return "caught"
                if p["after"] == "stop":
                    raise StopAsyncIteration
                if p["after"] == "await":
                    await Pause()
                raise ValueError
            return got

    def generator(self):
        # A generator-based coroutine, as types.coroutine makes one.
        try:
            got = yield from Pause().__await__()
        except KeyError:
            if p["after"] == "return":
                return "caught"
            if p["after"] == "stop":
                raise StopAsyncIteration
            if p["after"] == "await":
                yield from Pause().__await__()
            raise ValueError
        return got

    generator.__code__ = generator.__code__.replace(co_flags=generator.__code__.co_flags | 0x100)

    class Based(It):
        __anext__ = generator

    async def agen():
        try:
            got = await Pause()
        except KeyError:
            if p["after"] == "return":
                yield "caught"
            if p["after"] == "stop":
                return
            if p["after"] == "await":
                await Pause()
            raise ValueError
        yield got

    async def driver():
        source = {"coroutine": It, "generator": Based, "agen": agen}[p["source"]]()
        return await anext(source, "d")

    co = driver()
    co.send(None)
    assert type(co.cr_await).__name__ == "anext_awaitable"
    resume = p["resume"]
    try:
        if resume == "close":
            co.close()
            result = "closed"
        elif resume == "send":
            co.send("sent")
            result = "suspended"
        else:
            co.throw({"instance": KeyError("k"), "class": KeyError, "other": IndexError("i")}[resume])
            result = "suspended"
    except StopIteration as e:
        result = "value " + e.value
    except (ValueError, IndexError) as e:
        result = "raised " + type(e).__name__
    return "%s awaiting=%s" % (result, co.cr_await is not None)

check_programs(outcome)
