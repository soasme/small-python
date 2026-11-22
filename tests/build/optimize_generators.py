# build: -O
# bundles: optimize_generators.py
# description: Removing assertions preserves generator and async-generator function kinds in a standalone program.

def g():
    assert (yield 1)
    return 7


async def ag():
    assert (yield 1)


value = g()
if type(value).__name__ != "generator":
    raise SystemExit("optimized function stopped being a generator")
try:
    next(value)
except StopIteration as error:
    if error.value != 7:
        raise SystemExit("generator return value changed")
else:
    raise SystemExit("optimized assertion still yielded")

value = ag()
if type(value).__name__ != "async_generator":
    raise SystemExit("optimized function stopped being an async generator")
try:
    value.__anext__().send(None)
except StopAsyncIteration:
    pass
else:
    raise SystemExit("optimized async assertion still yielded")
