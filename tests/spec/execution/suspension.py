# spec: PLS-315 9.4, 9.5, 14.8, 18.1.2
# description: A running frame cannot be resumed; the handled exception follows frames and suspension.
from harness import *

def reentrant():
    yield me.send(None)
me = reentrant()
e = assert_raises(ValueError, next, me)
assert_eq(str(e), "generator already executing")

async def coroutine():
    myself.send(None)
myself = coroutine()
e = assert_raises(ValueError, myself.send, None)
assert_eq(str(e), "coroutine already executing")

# A suspended frame keeps its state.
def counter():
    total = 0
    while True:
        total += yield total
c = counter()
next(c)
c.send(3)
assert_eq(c.send(4), 7)

# The current handled exception: bare raise re-raises it, outside it is None.
def reraise():
    raise
e = assert_raises(RuntimeError, reraise)
assert_eq(str(e), "No active exception to reraise")
try:
    raise KeyError("k")
except KeyError:
    e = assert_raises(KeyError, reraise)
    assert_eq(e.args, ("k",))
# The nearest frame's handled exception wins; the previous one is restored after.
try:
    raise KeyError("outer")
except KeyError:
    try:
        raise IndexError("inner")
    except IndexError:
        assert_eq(assert_raises(IndexError, reraise).args, ("inner",))
    assert_eq(assert_raises(KeyError, reraise).args, ("outer",))

# An exception raised in a handler has the handled exception as __context__.
try:
    try:
        raise KeyError
    except KeyError:
        raise ValueError
except ValueError as v:
    assert_type(v.__context__, KeyError)

# A suspended generator keeps its handled exception and restores it when resumed.
def keeps():
    try:
        raise KeyError("in generator")
    except KeyError:
        yield
        raise
g = keeps()
next(g)
try:
    raise IndexError("caller")
except IndexError:
    e = assert_raises(KeyError, next, g)
    assert_eq(e.args, ("in generator",))
    assert_eq(assert_raises(IndexError, reraise).args, ("caller",))
# A generator resumed from a handler sees the caller's handled exception.
def sees():
    yield
    raise
g = sees()
next(g)
try:
    raise TypeError("caller")
except TypeError:
    assert_eq(assert_raises(TypeError, next, g).args, ("caller",))
