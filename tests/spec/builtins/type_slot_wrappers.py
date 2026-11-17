# spec: PLS-315 28.7
# description: a class binds type's special-method slots as method-wrapper
# objects, as any instance binds its type's, while type's
# __instancecheck__, __subclasscheck__ and __subclasses__ are method
# descriptors whose bound form is a builtin function, with or without a
# metaclass. Inside functions as at module level.
from harness import *

class C: pass
class M(type): pass
class D(metaclass=M): pass

def kinds():
    out = [type(type.__dict__[n]).__name__ for n in ("__call__", "__or__", "__instancecheck__", "__subclasscheck__", "__subclasses__")]
    for k in (C, int, D):
        out.append([type(getattr(k, n)).__name__ for n in ("__call__", "__instancecheck__", "__subclasscheck__", "__subclasses__")])
    out += [type(C.__or__).__name__, type(C.__ror__).__name__, repr(C.__call__).startswith("<method-wrapper '__call__' of type object at "),
            C.__call__() is not None, C.__subclasses__(), C.__instancecheck__(C())]
    return out

wrapped = ["method-wrapper", "builtin_function_or_method", "builtin_function_or_method", "builtin_function_or_method"]
expected = ["wrapper_descriptor", "wrapper_descriptor", "method_descriptor", "method_descriptor", "method_descriptor",
            wrapped, wrapped, wrapped, "method-wrapper", "method-wrapper", True, True, [], True]

def main():
    return kinds()

assert_eq(main(), expected)
assert_eq(kinds(), expected)
