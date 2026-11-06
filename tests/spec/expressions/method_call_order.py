# spec: PLS-315 13.3.4, 13.3.1
# description: A method call evaluates its primary, the attribute, before
# its arguments: the lookup's code runs first, a failing lookup raises
# before any argument runs, and an argument that rebinds the method does
# not change the callee, inside functions as at module level.
from harness import *

log = []

def arg(x):
    log.append('arg')
    return x

class Logged:
    @property
    def m(self):
        log.append('name')
        return lambda *a: a

def logged():
    o = Logged()
    first = o.m(arg(1))
    second = o.m(o.m)
    return first, len(second), log

assert logged() == ((1,), 1, ['name', 'arg', 'name', 'name']), log

class Plain:
    def m(self, x):
        return ('old', x)

def rebinding():
    p = Plain()
    def rebind(x):
        p.m = lambda x: ('new', x)
        return x
    return p.m(rebind(1)), p.m(2)

assert rebinding() == (('old', 1), ('new', 2))

def failing():
    del log[:]
    try:
        [].missing(arg(1))
    except AttributeError as e:
        return str(e), log

assert failing() == ("'list' object has no attribute 'missing'", [])

del log[:]
o = Logged()
assert o.m(arg(3)) == (3,) and log == ['name', 'arg']
