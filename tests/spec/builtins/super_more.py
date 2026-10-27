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
