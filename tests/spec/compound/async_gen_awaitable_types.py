# spec: PLS-315 27.5.1, 19.3.4
# description: The asend, athrow and anext awaitables' types define __await__, __iter__, __next__, send, throw and close; calling them through the type drives the generator as the bound methods do.
from harness import *

async def agen():
    yield 5

g = agen()
awaitables = [g.asend(None), g.athrow(ValueError), anext(agen(), 1)]
for aw in awaitables:
    cls = type(aw)
    for name in ("__await__", "__iter__", "__next__", "send", "throw", "close"):
        assert_true(name in cls.__dict__, (cls.__name__, name))
    assert_is(cls.__await__(aw), aw)
    assert_is(cls.__iter__(aw), aw)

asend, athrow, anext_aw = awaitables
e = assert_raises(StopIteration, type(asend).__next__, asend)
assert_eq(e.value, 5)
assert_raises(ValueError, type(athrow).__next__, athrow)
# The value of StopIteration is the yielded value, through the type as through the method.
e = assert_raises(StopIteration, type(anext_aw).__next__, anext_aw)
assert_eq(e.value, 5)
aw = anext(agen(), 1)
e = assert_raises(StopIteration, type(aw).send, aw, None)
assert_eq(e.value, 5)
e = assert_raises(TypeError, type(asend).send, 1, None)
assert_eq(str(e), "descriptor 'send' for 'async_generator_asend' objects doesn't apply to a 'int' object")
