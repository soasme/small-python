# spec: reference/expressions.html#primaries
# description: Attribute references, subscriptions, slicings, await, the power operator, and evaluation order.
from harness import *

# Attribute references call __getattribute__, then __getattr__ on AttributeError.
class Tracked:
    known = 1
    def __getattr__(self, name):
        return "fallback:" + name
obj = Tracked()
assert_eq((obj.known, obj.other), (1, "fallback:other"))
class Raising:
    @property
    def broken(self):
        raise AttributeError("inner")
    def __getattr__(self, name):
        return "recovered:" + name
assert_eq(Raising().broken, "recovered:broken")
class Strict:
    def __getattribute__(self, name):
        if name == "secret": raise AttributeError(name)
        return object.__getattribute__(self, name)
    value = 5
assert_eq(Strict().value, 5)
assert_raises(AttributeError, lambda: Strict().secret)
# Attribute names on int literals need a space or parentheses.
assert_eq((1 .real, (1).imag, 1.0.real), (1, 0, 1.0))
assert_syntax_error("1.real")
# The AttributeError carries name and obj.
e = assert_raises(AttributeError, lambda: obj.__class__.missing)
assert_eq((e.name, e.obj), ("missing", Tracked))

# Subscription: sequences take ints (or __index__), mappings any hashable key.
class Index:
    def __index__(self): return 1
assert_eq(([10, 20][Index()], "ab"[Index()], (1, 2)[-1], {(1, 2): "t"}[1, 2]), (20, "b", 2, "t"))
one, key_float, key_str = [1], 1.0, "0"
assert_raises(TypeError, lambda: one[key_float])
assert_raises(TypeError, lambda: one[key_str])
assert_raises(IndexError, lambda: [][0])
# A tuple of expressions is a tuple key; starred expressions are allowed (3.11).
class Echo:
    def __getitem__(self, key): return key
echo = Echo()
rest = (2, 3)
assert_eq((echo[1], echo[1,], echo[1, 2], echo[*rest], echo[0, *rest], echo[()]), (1, (1,), (1, 2), (2, 3), (0, 2, 3), ()))
# Slicings build slice objects, with None for omitted parts.
assert_eq((echo[1:2], echo[:], echo[::2], echo[1:2, 3], echo[..., 1:]), (slice(1, 2), slice(None), slice(None, None, 2), (slice(1, 2), 3), (Ellipsis, slice(1, None))))
# __class_getitem__ makes a class subscriptable; it is an implicit classmethod.
class Generic:
    def __class_getitem__(cls, item): return (cls.__name__, item)
assert_eq(Generic[int], ("Generic", int))
assert_eq((list[int].__origin__, dict[str, int].__args__), (list, (str, int)))
# A metaclass __getitem__ takes priority over __class_getitem__.
class Meta(type):
    def __getitem__(cls, item): return "meta"
class WithMeta(metaclass=Meta):
    def __class_getitem__(cls, item): return "class"
assert_eq(WithMeta[0], "meta")
e = assert_raises(TypeError, lambda: object()[0])
assert_eq(str(e), "'object' object is not subscriptable")
e = assert_raises(TypeError, lambda: int[0][0] if False else len[0])
assert_eq(str(e), "'builtin_function_or_method' object is not subscriptable")
# Negative indexes are adjusted by the sequence, not by the subscription.
class Raw:
    def __getitem__(self, i): return i
    def __len__(self): return 10
assert_eq(Raw()[-1], -1)

# Slice assignment and deletion on user objects go through __setitem__/__delitem__.
class Recorder:
    def __init__(self): self.log = []
    def __setitem__(self, key, value): self.log.append(("set", key, value))
    def __delitem__(self, key): self.log.append(("del", key))
r = Recorder()
r[1:2] = "x"
del r[::3]
r[1, 2] = 0
assert_eq(r.log, [("set", slice(1, 2), "x"), ("del", slice(None, None, 3)), ("set", (1, 2), 0)])

# The power operator binds tighter than unary minus on its left, looser on its right.
assert_eq((-2 ** 2, 2 ** -1, (-2) ** 2, 2 ** 3 ** 2, -2 ** -2), (-4, 0.5, 4, 512, -0.25))
assert_eq(((-8) ** (1 / 3)).real > 0, True)  # a negative base with a fractional exponent is complex
assert_type((-8) ** 0.5, complex)
assert_eq((0 ** 0, 0.0 ** 0, 2 ** 0.5 == 2 ** (1 / 2), pow(-1, 0.5) == 1j or True), (1, 1.0, True, True))
class Power:
    def __pow__(self, other, mod=None): return ("pow", other, mod)
    def __rpow__(self, other, mod=None): return ("rpow", other, mod)
assert_eq((Power() ** 2, 2 ** Power(), pow(Power(), 2, 5)), (("pow", 2, None), ("rpow", 2, None), ("pow", 2, 5)))
assert_eq(pow(2, Power(), 5), ("rpow", 2, 5))  # three-argument pow tries __rpow__ (3.14)

# await is valid only in a coroutine function; it suspends on __await__.
class Awaitable:
    def __await__(self):
        value = yield "suspended"
        return value * 2
async def waiter():
    return await Awaitable()
coroutine = waiter()
assert_eq(coroutine.send(None), "suspended")
try:
    coroutine.send(21)
except StopIteration as stop:
    assert_eq(stop.value, 42)
async def bad_await():
    await 1
e = assert_raises(TypeError, bad_await().send, None)
assert_eq(str(e), "'int' object can't be awaited")
class BadIterator:
    def __await__(self): return 1
async def bad_iterator():
    await BadIterator()
e = assert_raises(TypeError, bad_iterator().send, None)
assert_eq(str(e), "BadIterator.__await__() must return an iterator, not int")
assert_syntax_error("await x\n")
assert_syntax_error("def f():\n    await x\n")
assert_syntax_error("async def f():\n    def g():\n        await x\n")
assert_syntax_error("async def f():\n    lambda: await x\n")
assert_compiles("async def f():\n    [await x for x in y]\n")
# await binds tighter than ** on its right and unary minus.
async def precedence():
    return -await Ready(2) ** 2
class Ready:
    def __init__(self, v): self.v = v
    def __await__(self):
        return self.v
        yield
try:
    precedence().send(None)
except StopIteration as stop:
    assert_eq(stop.value, -4)

# Evaluation order: left to right, with the right side of an assignment first.
order = []
def mark(name, value=None):
    order.append(name)
    return value if value is not None else name
mark("a") + mark("b") * mark("c", 2)
assert_eq(order, ["a", "b", "c"])
order.clear()
target = {}
target[mark("key")] = mark("value")
assert_eq(order, ["value", "key"])
order.clear()
mark("f", lambda *a, **k: None)(mark("x"), *mark("y", [1]), z=mark("z"), **mark("w", {}))
assert_eq(order, ["f", "x", "y", "z", "w"])
order.clear()
{mark("k1"): mark("v1"), mark("k2"): mark("v2")}
assert_eq(order, ["k1", "v1", "k2", "v2"])
order.clear()
mark("obj", Recorder())[mark("i", 0)] = mark("rhs", 1)
assert_eq(order, ["rhs", "obj", "i"])
order.clear()
# In an augmented assignment the target is evaluated before the value, once.
holder = [0]
mark("container", holder)[mark("index", 0)] += mark("amount", 5)
assert_eq((order, holder), (["container", "index", "amount"], [5]))
order.clear()
# Comparison operands left to right; chained operands at most once.
mark("p", 1) < mark("q", 2) < mark("r", 3)
assert_eq(order, ["p", "q", "r"])
order.clear()
# Conditional: condition first, then one branch.
mark("yes") if mark("cond", 1) else mark("no")
assert_eq(order, ["cond", "yes"])
