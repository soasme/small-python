# spec: reference/expressions.html#private-name-mangling
# description: __names in class bodies are mangled with the class name; edge cases.
from harness import *

class Ham:
    __x = 1
    def __m(self):
        return 2
    def get(self):
        return self.__x, self.__m(), __class__.__x
    def setter(self):
        self.__y = 3
        return self._Ham__y
assert_eq(Ham().get(), (1, 2, 1))
assert_eq(Ham().setter(), 3)
assert_eq(sorted(k for k in vars(Ham) if k.startswith("_Ham")), ["_Ham__m", "_Ham__x"])

# Leading underscores of the class name are stripped; names ending in __ are not mangled.
class _Under:
    __a = 1
    __b__ = 2
assert_true(hasattr(_Under, "_Under__a"))
assert_true(hasattr(_Under, "__b__"))
class ___:
    __c = 3
assert_true(hasattr(___, "__c"))  # a class name of only underscores does not mangle

# Mangling applies in nested functions, comprehensions, and to names in any position.
class Outer:
    def method(self):
        __local = 5
        return [__local for _ in range(1)], (lambda: __local)()
    def keyword(self):
        def g(**kw):
            return kw
        return g(__key=1)
    def attribute(self, obj):
        return obj.__secret
assert_eq(Outer().method(), ([5], 5))
assert_eq(Outer().keyword(), {"__key": 1})  # keyword argument names are not mangled
class Holder:
    _Outer__secret = "found"
assert_eq(Outer().attribute(Holder()), "found")

# Imported names are mangled too: `import __spam` binds _Outer__spam (checked by compile).
ns = run("class C:\n    def f(self):\n        global __g\n        __g = 1\nC().f()\n")
assert_true("_C__g" in ns)

# Nested classes use the innermost class name.
class A:
    class B:
        __z = 1
    __w = 2
assert_true(hasattr(A.B, "_B__z"))
assert_true(hasattr(A, "_A__w"))

# Dotted attribute names via getattr are not mangled.
class G:
    def get(self):
        return getattr(self, "__q", None)
    __q = 1
assert_is(G().get(), None)
