# spec: PLS-315 16.6.2
# description: reading __annotations__ of a class whose metaclass
# inherits type's calls the class's __annotate__, which may call a
# Python function that loops, once, and caches the dict; a metaclass's
# own __annotations__, a property or a plain value, answers instead, and
# a metaclass __getattribute__ sees the getter read __annotate__. A
# class without annotations caches an empty dict and keeps None as
# __annotate_func__. A non-dict result is a TypeError and an exception
# propagates. Inside functions as at module level.
from harness import *

log = []

def note(x):
    for _ in (): pass
    log.append(x)
    return x

class M(type): pass

class P(type):
    @property
    def __annotations__(cls): return {"meta": 1}

class V(type):
    __annotations__ = {"plain": 2}

class G(type):
    def __getattribute__(cls, name):
        if name.startswith("__annot"): log.append(name)
        return super().__getattribute__(name)

class Namespace(dict): pass

class N(type):
    @classmethod
    def __prepare__(m, name, bases): return Namespace()

def classes():
    class A(metaclass=M):
        x: note(int) = 1
    class B(metaclass=P):
        y: note(str)
    class C(metaclass=G):
        z: note(float)
    class D(metaclass=N):
        if 1:
            w: note(bytes) = 2
    class E(A): v: note(list)
    class F(metaclass=V):
        u: note(dict)
    return A, B, C, D, E, F

A, B, C, D, E, F = classes()
assert_eq(F.__annotations__, {"plain": 2})
assert_eq([A.__annotations__, A.__annotations__, B.__annotations__], [{"x": int}, {"x": int}, {"meta": 1}])
assert_eq(log, [int])
log.clear()
assert_eq([C.__annotations__, D.__annotations__, E.__annotations__], [{"z": float}, {"w": bytes}, {"v": list}])
assert_eq(log, ["__annotations__", "__annotate__", float, bytes, list])
assert_true(A.__annotations__ is A.__dict__["__annotations_cache__"])

class Plain: pass
empty = Plain.__annotations__
assert_eq((empty, Plain.__annotations__ is empty, Plain.__dict__["__annotate_func__"]), ({}, True, None))

def errors():
    out = []
    class Bad(metaclass=M):
        x: 1/0
    try: Bad.__annotations__
    except ZeroDivisionError: out.append("ZeroDivisionError")
    class Wrong(metaclass=M): pass
    Wrong.__annotate__ = lambda format: 5
    try: Wrong.__annotations__
    except TypeError as e: out.append(str(e))
    return out

assert_eq(errors(), ["ZeroDivisionError", "__annotate__() must return a dict, not int"])
