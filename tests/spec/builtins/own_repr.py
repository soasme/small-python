# spec: PLS-315 7.5.6, 28.7
# description: built-in types hold their own __repr__, so an explicit call gives repr.
from harness import *


def gen(): yield
async def coro(): pass
async def agen(): yield
class C:
    def method(self): pass
def outer():
    x = 1
    return lambda: x
co = coro()
samples = [len, [].append, C().method, outer, outer().__closure__[0], outer.__code__, gen(), co, agen(),
           super(C, C()), C, __import__("harness"), str.join, str.__add__, (1).__add__, b"a", bytearray(b"a")]
co.close()
for value in samples:
    assert_eq("__repr__" in type(value).__dict__, True, type(value).__name__)
    assert_eq(type(value).__repr__(value), repr(value))
assert_eq((b"a".__str__(), bytearray(b"a").__str__(), "a".__str__()), ("b'a'", "bytearray(b'a')", "a"))

# The descriptor types check their receiver (28.7), for __call__ too.
method_descriptor, wrapper_descriptor, method_wrapper = type(str.join), type(str.__add__), type((1).__add__)
for kind in (method_descriptor, wrapper_descriptor, method_wrapper):
    name = kind.__name__
    for method in ("__call__", "__repr__"):
        assert_raises(TypeError, getattr(kind, method), message="descriptor '%s' of '%s' object needs an argument" % (method, name))
        assert_raises(TypeError, getattr(kind, method), 1,
                      message="descriptor '%s' requires a '%s' object but received a 'int'" % (method, name))
assert_eq(method_descriptor.__call__(str.join, "-", "ab"), "a-b")
assert_raises(TypeError, method_descriptor.__repr__, str.join, 1, message="expected 0 arguments, got 1")
assert_raises(TypeError, lambda: method_descriptor.__repr__(str.join, x=1), message="wrapper __repr__() takes no keyword arguments")
