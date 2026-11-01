# spec: PLS-315 7.4.4, 21.1.2, 21.1.4, 21.1.5, 20.1
# description: Built-in methods and constructors called through their class with a missing or foreign first argument.
from harness import *

def check(message, function, *args):
    assert_raises(TypeError, function, *args, message=message)

Proxy = type(type.__dict__)
for cls, name in ((memoryview, "memoryview"), (Proxy, "mappingproxy")):
    check(f"{name}.__new__(): not enough arguments", cls.__new__)
    check(f"{name}.__new__(X): X is not a type object (int)", cls.__new__, 1)
    check(f"{name}.__new__(int): int is not a subtype of {name}", cls.__new__, int)
check("descriptor 'tobytes' for 'memoryview' objects doesn't apply to a 'int' object", memoryview.tobytes, 1)
check("unbound method memoryview.tobytes() needs an argument", memoryview.tobytes)
check("descriptor 'keys' for 'mappingproxy' objects doesn't apply to a 'int' object", Proxy.keys, 1)
check("unbound method mappingproxy.keys() needs an argument", Proxy.keys)
check("expected a memoryview object", memoryview(b"").__release_buffer__, 1)
check("expected a memoryview object", bytearray().__release_buffer__, 1)

check("descriptor '__getattribute__' of 'object' object needs an argument", object.__getattribute__)
check("expected 1 argument, got 0", object.__getattribute__, 1)
check("expected 1 argument, got 2", object.__getattribute__, 1, "a", 2)
check("attribute name must be string, not 'int'", object.__getattribute__, 1, 2)
check("__setattr__ expected 2 arguments, got 1", object.__setattr__, 1, "a")
check("attribute name must be string, not 'int'", object.__setattr__, 1, 2, 3)
check("descriptor '__delattr__' of 'object' object needs an argument", object.__delattr__)
check("descriptor '__getattribute__' of 'type' object needs an argument", type.__getattribute__)
check("expected 1 argument, got 0", type.__getattribute__, int)
check("attribute name must be string, not 'int'", type.__getattribute__, int, 1)
check("__setattr__ expected 2 arguments, got 1", type.__setattr__, int, "a")
check("descriptor '__getattribute__' requires a 'type' object but received a 'int'", type.__getattribute__, 1, "a")
class Name(str): pass
assert_eq(object.__getattribute__(1, Name("real")), 1)
assert_eq(type.__getattribute__(int, Name("__name__")), "int")

check("descriptor 'with_traceback' for 'BaseException' objects doesn't apply to a 'int' object", BaseException.with_traceback, 1, None)
check("unbound method BaseException.with_traceback() needs an argument", BaseException.with_traceback)
check("BaseException.with_traceback() takes exactly one argument (0 given)", BaseException.with_traceback, ValueError())
check("descriptor 'add_note' for 'BaseException' objects doesn't apply to a 'int' object", BaseException.add_note, 1, "x")
check("unbound method BaseException.add_note() needs an argument", BaseException.add_note)
check("BaseException.add_note() takes exactly one argument (0 given)", BaseException.add_note, ValueError())
check("BaseException.add_note() takes exactly one argument (2 given)", BaseException.add_note, ValueError(), 1, 2)
check("add_note() argument must be str, not int", BaseException.add_note, ValueError(), 1)
check("descriptor '__init__' requires a 'BaseException' object but received a 'int'", BaseException.__init__, 1)
check("descriptor '__init__' of 'BaseException' object needs an argument", BaseException.__init__)
check("descriptor '__init__' requires a 'SyntaxError' object but received a 'ValueError'", SyntaxError.__init__, ValueError())
check("cannot set 1 attribute of immutable type 'int'", type.__setattr__, int, 1, 2)
check("cannot set 1 attribute of immutable type 'int'", type.__delattr__, int, 1)
check("attribute name must be string, not 'int'", type.__setattr__, Name, 1, 2)
check("unbound method str.join() needs an argument", str.join)
check("descriptor 'join' for 'str' objects doesn't apply to a 'int' object", str.join, 1, [])
check("unbound method property.getter() needs an argument", property.getter)
check("unbound method property.__set_name__() needs an argument", property.__set_name__)
check("descriptor 'getter' for 'property' objects doesn't apply to a 'int' object", property.getter, 1, None)
for cls in (classmethod, staticmethod):
    check(f"descriptor '__get__' of '{cls.__name__}' object needs an argument", cls.__get__)
    check(f"descriptor '__get__' requires a '{cls.__name__}' object but received a 'int'", cls.__get__, 1, None)
check("unbound method type.__subclasses__() needs an argument", type.__subclasses__)
check("descriptor '__subclasses__' for 'type' objects doesn't apply to a 'int' object", type.__subclasses__, 1)
