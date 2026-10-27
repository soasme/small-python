# spec: PLS-315 13.3.4
# description: Argument unpacking, evaluation order, keyword rules, and callable objects.
from harness import *

def show(*args, **kwargs): return args, kwargs
assert_eq(show(*[1, 2], 3, *(4,)), ((1, 2, 3, 4), {}))
assert_eq(show(**{"a": 1}, b=2, **{"c": 3}), ((), {"a": 1, "b": 2, "c": 3}))
assert_eq(show(1, *[2], x=1, *[3], **{"y": 2}), ((1, 2, 3), {"x": 1, "y": 2}))
e = assert_raises(TypeError, lambda: show(**{"a": 1}, a=2))
assert_true(str(e).endswith("show() got multiple values for keyword argument 'a'"))
e = assert_raises(TypeError, lambda: show(**{"a": 1}, **{"a": 2}))
assert_true(str(e).endswith("show() got multiple values for keyword argument 'a'"))
e = assert_raises(TypeError, lambda: show(*1))
assert_eq(str(e), "Value after * must be an iterable, not int")
e = assert_raises(TypeError, lambda: show(**1))
assert_eq(str(e), "Value after ** must be a mapping, not int")
e = assert_raises(TypeError, lambda: show(**{1: 2}))
assert_eq(str(e), "keywords must be strings")
assert_syntax_error("f(a=1, a=2)")
assert_syntax_error("f(a=1, 2)")
assert_syntax_error("f(**k, *a)")
assert_syntax_error("f(**k, 1)")
assert_syntax_error("f(x for x in y, 1)")
assert_syntax_error("f(1, x for x in y)")
assert_syntax_error("f(a + 1 = 2)")
assert_syntax_error("f(True=1)")
assert_compiles("f(x for x in y)")
assert_compiles("f(*a, b, *c, d=1, **e, f=2)")
assert_eq(show(x for x in [1])[0][0].__class__.__name__, "generator")

# Mapping unpacking uses keys() and __getitem__.
class Mapping:
    def keys(self): return ["k"]
    def __getitem__(self, key): return key.upper()
assert_eq(show(**Mapping()), ((), {"k": "K"}))

# Evaluation order: function, then arguments left to right.
order = []
def trace(value):
    order.append(value)
    return value
def target(*a, **k): return a, k
trace(target)(trace(1), *trace([2]), k=trace(3), **trace({"m": 4}))
assert_eq(order, [target, 1, [2], 3, {"m": 4}])

class Callable:
    def __call__(self, x): return ("called", x)
assert_eq(Callable()(1), ("called", 1))
instance = Callable()
instance.__call__ = lambda x: "instance attribute"
assert_eq(instance(1), ("called", 1))  # implicit lookup uses the type
one = 1
e = assert_raises(TypeError, lambda: one())
assert_eq(str(e), "'int' object is not callable")
e = assert_raises(TypeError, lambda: object()())
assert_eq(str(e), "'object' object is not callable")
# Bound methods carry self.
class C:
    def m(self, x): return (self, x)
c = C()
assert_eq(c.m(1), (c, 1))
bound = c.m
assert_is(bound.__self__, c)
assert_is(bound.__func__, C.m)
assert_eq(C.m(c, 2), (c, 2))
e = assert_raises(TypeError, C.m)
assert_eq(str(e), "C.m() missing 2 required positional arguments: 'self' and 'x'")
