# spec: PLS-315 20.3
# description: super() in methods and class methods.
from harness import *
test_super_list = super(list)
assert test_super_list.__self__ is None
assert test_super_list.__self_class__ is None
assert test_super_list.__thisclass__ == list


class testA:
    a = 1


class testB(testA):
    b = 1


superB = super(testB)
assert superB.__thisclass__ == testB
assert superB.__self_class__ is None
assert superB.__self__ is None
# super() checks its arguments with CPython's messages.
class Other: pass
assert_eq(str(assert_raises(TypeError, super, 1)), "super() argument 1 must be a type, not int")
assert_eq(str(assert_raises(TypeError, super, int, "a")),
          "super(type, obj): obj (instance of str) is not an instance or subtype of type (int).")
assert_eq(str(assert_raises(TypeError, super, int, Other)),
          "super(type, obj): obj (type Other) is not an instance or subtype of type (int).")

# Deleting the __class__ cell through nonlocal leaves it empty, for super()
# and for reads of the free variable.
class Emptied:
    def f(self):
        nonlocal __class__
        del __class__
        try:
            super()
        except RuntimeError as e:
            assert_eq(str(e), "super(): empty __class__ cell")
        else:
            assert_true(False, "super() with an empty cell")
        e = assert_raises(NameError, lambda: __class__)
        assert_eq(str(e), "cannot access free variable '__class__' where it is not associated with a value in enclosing scope")
        return __class__
assert_eq(str(assert_raises(NameError, Emptied().f)),
          "cannot access free variable '__class__' where it is not associated with a value in enclosing scope")
assert_raises(ValueError, lambda: Emptied.f.__closure__[0].cell_contents)

# super() binds a built-in base class's methods to the subclass instance.
class Text(str): pass
text = Text("ab")
for name in ("__getattribute__", "upper"):
    assert_is(getattr(super(Text, text), name).__self__, text)
assert_eq(super(Text, text).upper(), "AB")
assert_raises(AttributeError, super(Text, text).__getattribute__, "real", message="'Text' object has no attribute 'real'")
class Items(list): pass
items = Items([1])
super(Items, items).append(2)
assert_eq(items, [1, 2])

# super() past a built-in base: a name it lacks continues to the next class.
class Listed(list):
    def missing(self): return super().bogus
    def present(self): return super().append
assert_raises(AttributeError, Listed().missing, message="'super' object has no attribute 'bogus'")
present = Listed().present()
present(1)
assert_eq(present.__self__, [1])
