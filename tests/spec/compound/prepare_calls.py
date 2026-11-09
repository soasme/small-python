# spec: PLS-315 16.4.1, 16.4.2
# description: A metaclass's __prepare__ is called with the class name,
# the bases and the class keywords but metaclass, by its classmethod's
# class, as a plain function or through a callable instance, and its
# mapping is the namespace the body runs in, whether the body calls,
# loops or only assigns; a result that is not a mapping raises
# TypeError, and its exception propagates, inside functions as at module
# level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Meta(type):
    @classmethod
    def __prepare__(mcls, name, bases, **kw):
        spin()
        log.append((mcls.__name__, name, len(bases), kw))
        return {"injected": 1}
    def __new__(mcls, name, bases, ns, **kw):
        return super().__new__(mcls, name, bases, ns)
    def __init__(cls, name, bases, ns, **kw):
        super().__init__(name, bases, ns)

class Plain(type):
    def __prepare__(name, bases):
        spin()
        return {"p": name}

class Bad(type):
    @classmethod
    def __prepare__(m, n, b): return 1

class Raise(type):
    @classmethod
    def __prepare__(m, n, b):
        spin()
        raise KeyError("prep")

class Callable:
    def __call__(self, name, bases): return {"z": len(bases)}

class Instance(type):
    __prepare__ = Callable()

def error(make):
    try:
        return make()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    class A(metaclass=Meta, flag=2):
        x = injected + 1
    class B(A):
        y = injected
        for i in range(2): spin()
    class C(metaclass=Plain):
        q = p
    def bad():
        class D(metaclass=Bad): pass
    def raised():
        class E(metaclass=Raise): spin()
    class F(object, metaclass=Instance):
        w = z
    return [A.x, B.y, B.i, C.q, error(bad), error(raised), F.w, type(B).__name__, list(log)]

expected = [2, 1, 1, 'C', ('TypeError', 'Bad.__prepare__() must return a mapping, not int'), ('KeyError', "'prep'"), 1, 'Meta',
            [('Meta', 'A', 0, {'flag': 2}), ('Meta', 'B', 1, {})]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
