# spec: PLS-315 10.4.1, 7.3.7, 7.3.9, 7.3.6
# description: type's own __getattribute__, __setattr__ and __delattr__; a metaclass's hooks run for its classes' attribute assignment and deletion.
from harness import *

# type defines all three slots itself.
for name in ("__getattribute__", "__setattr__", "__delattr__"):
    assert_true(name in type.__dict__, name)
    assert_true(type.__dict__[name] is not object.__dict__[name], name)
    e = assert_raises(TypeError, getattr(type, name), 1, "x", *((1,) if name == "__setattr__" else ()))
    assert_eq(str(e), "descriptor '%s' requires a 'type' object but received a 'int'" % name)

class Plain: pass
type.__setattr__(Plain, "a", 1)
assert_eq((Plain.a, type.__getattribute__(Plain, "a")), (1, 1))
type.__delattr__(Plain, "a")
assert_false(hasattr(Plain, "a"))
assert_eq(str(assert_raises(TypeError, type.__setattr__, int, "x", 1)), "cannot set 'x' attribute of immutable type 'int'")
assert_eq(str(assert_raises(TypeError, type.__delattr__, int, "real")), "cannot set 'real' attribute of immutable type 'int'")

# object's versions refuse a class.
assert_eq(str(assert_raises(TypeError, object.__setattr__, Plain, "x", 1)), "can't apply this __setattr__ to type object")
assert_eq(str(assert_raises(TypeError, object.__delattr__, Plain, "x")), "can't apply this __delattr__ to type object")

# A metaclass's __setattr__ and __delattr__ run for assignment, deletion,
# setattr() and delattr() on its classes; super() reaches type's.
log = []
class Meta(type):
    def __setattr__(cls, name, value):
        log.append(("set", name, value))
        super().__setattr__(name, value)
    def __delattr__(cls, name):
        log.append(("del", name))
        super().__delattr__(name)
class C(metaclass=Meta):
    body = 1
assert_eq(log, [])
C.x = 1
setattr(C, "y", 2)
del C.x
delattr(C, "y")
assert_eq(log, [("set", "x", 1), ("set", "y", 2), ("del", "x"), ("del", "y")])
assert_false(hasattr(C, "x") or hasattr(C, "y"))
# Subclasses use their metaclass's hooks; instances use their own class's.
class D(C): pass
D.z = 3
assert_eq(log[-1], ("set", "z", 3))
C().w = 4
assert_eq(log[-1], ("set", "z", 3))

# A hook can refuse.
class Frozen(type):
    def __setattr__(cls, name, value): raise AttributeError("frozen " + name)
class F(metaclass=Frozen): pass
assert_eq(str(assert_raises(AttributeError, setattr, F, "a", 1)), "frozen a")
assert_false("a" in F.__dict__)

# super() over a metaclass chain reaches type's slots.
class Base(type): pass
made = Base("made", (Base,), {})
super(Base, type(made)).__setattr__(made, "bar", 1)
assert_eq((made.bar, super(Base, type(made)).__getattribute__(made, "bar")), (1, 1))
