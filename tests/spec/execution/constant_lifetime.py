# spec: PLS-315 9.7, 27.2, 27.3, 28.2
# description: Compiled numeric constants survive release of the source and code
# references, collection during argument evaluation, and suspended execution.
from harness import *

def choose(first, second):
    return second

def collect():
    host.collect()
    return None

for literal in ("123456789012345678901234567890", "0xabcdef0123456789",
                "1.25", "2.5j", "-0.0", "-123456789012345678901234567890"):
    expected = eval(literal)
    for kind in ("function", "generator", "coroutine"):
        head = "async def" if kind == "coroutine" else "def"
        operation = "yield" if kind == "generator" else "return"
        source = head + " f():\n"
        if kind == "generator":
            source += "    yield None\n"
        source += "    " + operation + " choose(collect(), " + literal + ")\n"
        code = compile(source, "<constant-lifetime>", "exec")
        namespace = {"choose": choose, "collect": collect}
        exec(code, namespace)
        function = namespace.pop("f")
        del code, source, namespace
        collect()
        if kind == "function":
            value = function()
        else:
            suspended = function()
            del function
            if kind == "generator":
                assert next(suspended) is None
                collect()
                value = next(suspended)
                suspended.close()
            else:
                collect()
                try:
                    suspended.send(None)
                except StopIteration as error:
                    value = error.value
                else:
                    assert False, "coroutine did not return"
        assert type(value) is type(expected)
        assert repr(value) == repr(expected)
        collect()
        assert repr(value) == repr(expected)
