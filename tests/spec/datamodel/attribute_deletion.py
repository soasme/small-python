# spec: PLS-315 7.3.9, 19.3.11, 25.3.1, 25.4.1, 20.5.1, 28.9, 27.1.2
# description: Deleting missing and read-only attributes, and a sequence iterator whose type loses __getitem__.
from harness import *

def check(error, message, function, *args):
    assert_eq(str(assert_raises(error, function, *args)), message)

# A missing attribute is named after the object, whatever its metaclass.
class Meta(type): pass
class Klass(metaclass=Meta): pass
check(AttributeError, "type object 'Klass' has no attribute 'nope'", delattr, Klass, "nope")
check(AttributeError, "type object 'Meta' has no attribute 'nope'", delattr, Meta, "nope")
check(AttributeError, "'Klass' object has no attribute 'nope'", delattr, Klass(), "nope")

# Read-only data attributes of built-in objects.
check(AttributeError, "readonly attribute", delattr, slice(1), "start")
check(AttributeError, "readonly attribute", delattr, range(1), "start")
check(TypeError, "cannot set 'x' attribute of immutable type 'module'", delattr, type(__import__("builtins")), "x")
try:
    1 / 0
except ZeroDivisionError as error:
    traceback = error.__traceback__
check(AttributeError, "attribute 'tb_lineno' of 'traceback' objects is not writable", delattr, traceback, "tb_lineno")
check(TypeError, "can't delete tb_next attribute", delattr, traceback, "tb_next")
documented = property(doc="text")
del documented.__doc__
assert_eq(documented.__doc__, None)

# The iterator indexes its sequence through the type as it is at each step.
class Sequence:
    def __getitem__(self, index):
        if index > 1:
            raise IndexError
        return index
iterator = iter(Sequence())
assert_eq(next(iterator), 0)
del Sequence.__getitem__
check(TypeError, "'Sequence' object does not support indexing", next, iterator)
check(TypeError, "'Sequence' object is not subscriptable", lambda: Sequence()[0])
