# Compile and call each function; inspect the resulting object, not just flags.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def outcome(program):
    source = ("async def" if program["asynchronous"] else "def") + " f():\n"
    source += "    def inner(x=" + ("(yield None)" if program["defaultYield"] else "None") + "):\n"
    if program["nestedYield"]:
        source += "        yield 1\n"
    source += "        return 11\n"
    if program["ownYield"]:
        source += "    assert (yield 2)\n" if program["optimized"] else "    if False: yield 2\n"
    source += "    return" + (" 7" if program["valuedReturn"] else "") + "\n"
    namespace = {}
    try:
        exec(compile(source, "<function-scopes>", "exec", optimize=int(program["optimized"])), namespace)
    except SyntaxError as error:
        assert error.msg == "'return' with value in async generator"
        return "SyntaxError"
    value = namespace["f"]()
    kind = type(value).__name__
    if kind in ("generator", "coroutine"):
        value.close()
    elif kind == "async_generator":
        try:
            value.aclose().send(None)
        except StopIteration:
            pass
        else:
            raise AssertionError("close did not complete")
    else:
        assert value == (7 if program["valuedReturn"] else None)
        kind = "plain"
    return kind


check_programs(outcome)
