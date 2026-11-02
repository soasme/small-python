# spec: PLS-315 7.4.1
# description: calling a module suggests the callable attribute named after it.
import harness
from harness import *

ModuleType = type(harness)
def message(target):
    return str(assert_raises(TypeError, target))

m = ModuleType("m")
assert_eq(message(m), "'module' object is not callable")
m.m = 42
assert_eq(message(m), "'module' object is not callable")
m.m = print
assert_eq(message(m), "'module' object is not callable. Did you mean: 'm.m(...)'?")
del m.__name__
assert_eq(message(m), "'module' object is not callable")
m.__name__ = 42
assert_eq(message(m), "'module' object is not callable")
class S(str):
    pass
m.__name__ = S("m")
assert_eq(message(m), "'module' object is not callable. Did you mean: 'm.m(...)'?")
class Sub(ModuleType):
    pass
s = Sub("s")
s.s = print
assert_eq(message(s), "'Sub' object is not callable")
def missing(name):
    raise ValueError(name)
g = ModuleType("g")
g.__getattr__ = missing
assert_eq(message(g), "'module' object is not callable")
