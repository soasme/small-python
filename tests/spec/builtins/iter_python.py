# spec: PLS-315 19.3.23, 27.1.1
# description: iter() calls a class's Python __iter__ once and checks that it returned an iterator, however the call is spelled.
from harness import *

calls = []
class Items:
    def __iter__(self):
        calls.append("iter")
        return iter([1, 2])
assert_eq(list(iter(Items())), [1, 2])
items = Items()
assert_eq(next(iter(items)), 1)
spelled = iter
assert_eq(list(spelled(Items())), [1, 2])
assert_eq(calls, ["iter"] * 3)

# Its value may be any iterator; anything else is a TypeError.
class Gen:
    def __iter__(self):
        yield 3
assert_eq(list(iter(Gen())), [3])
class Bad:
    def __iter__(self):
        return 5
assert_raises(TypeError, iter, Bad(), message=f"{fqname(Bad)}.__iter__() must return an iterator, not int")
with Raises(TypeError, f"{fqname(Bad)}.__iter__() must return an iterator, not int"):
    iter(Bad())

# Its own exception, and a failure to bind it, propagate.
class Raising:
    def __iter__(self):
        raise KeyError("k")
with Raises(KeyError, "'k'"):
    iter(Raising())
class Unbound:
    def __iter__(self, needed):
        return iter(())
with Raises(TypeError, "Unbound.__iter__() missing 1 required positional argument: 'needed'"):
    iter(Unbound())

# In a generator, the call is the generator's.
def gen():
    yield next(iter(Items()))
assert_eq(list(gen()), [1])
