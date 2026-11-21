# Constants loaded after collection, through a function or suspended instance.
from harness import host

FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def choose(first, second):
    return second


def collect():
    host.collect()
    return None


def outcome(program):
    kind = program["kind"]
    head = "async def" if kind == "coroutine" else "def"
    operation = "yield" if kind == "generator" else "return"
    source = head + " f():\n"
    if kind == "generator":
        source += "    yield None\n"
    source += "    " + operation + " choose(collect(), " + program["literal"] + ")\n"
    code = compile(source, "<constant-load>", "exec")
    namespace = {"choose": choose, "collect": collect}
    exec(code, namespace)
    function = namespace.pop("f")
    del source, code, namespace
    collect()
    value = function()
    del function
    if kind == "generator":
        assert next(value) is None
        collect()
        result = next(value)
        value.close()
        value = result
    elif kind == "coroutine":
        collect()
        try:
            value.send(None)
        except StopIteration as error:
            value = error.value
        else:
            raise AssertionError("coroutine did not return")
    collect()
    return repr(value)


check_programs(outcome)
