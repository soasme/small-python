# spec: PLS-315 28.7, 27.2
# description: a generator's, coroutine's and async generator's special
# methods read from the instance are method-wrappers, as list's are, with
# their descriptor's __name__, __qualname__ and __objclass__, a read-only
# __self__ and no __module__; send, throw and close are builtin methods.
from harness import assert_eq

def attempt(f):
    try: return f()
    except AttributeError as e: return str(e)

def g(): yield 1
async def co(): pass
async def ag(): yield 1

x, c, a = g(), co(), ag()
wrappers = [x.__next__, x.__iter__, c.__await__, a.__aiter__, a.__anext__]
assert_eq([type(m).__name__ for m in wrappers], ["method-wrapper"] * 5)
assert_eq(type(x.__next__) is type([].__len__), True)
assert_eq([type(m).__name__ for m in (x.send, x.throw, x.close)], ["builtin_function_or_method"] * 3)
m = x.__next__
assert_eq((m.__name__, m.__qualname__, m.__objclass__, m.__self__ is x), ("__next__", "generator.__next__", type(x), True))
assert_eq(attempt(lambda: m.__module__), "'method-wrapper' object has no attribute '__module__'")
assert_eq(attempt(lambda: setattr(m, "__self__", 1)), "readonly attribute")
assert_eq((x.send.__module__, attempt(lambda: x.send.__objclass__)), (None, "'builtin_function_or_method' object has no attribute '__objclass__'"))
c.close()
