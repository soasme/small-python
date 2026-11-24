# spec: PLS-315 29.2.1, 29.2.2, 29.3, 29.4, 29.6, 5.2.6
# description: TypeVar, TypeVarTuple, ParamSpec and TypeAliasType called
# directly take the __name__ of their caller's globals as __module__, from
# a function or another namespace's code; those a type parameter list
# makes are typing's. A name that is not a str is a TypeError naming the
# argument's class by its name.
from harness import *
def f[T, *Ts, **P](): pass
T, Ts, P = f.__type_params__
type X = int
TV, TVT, PS, TAT = type(T), type(Ts), type(P), type(X)
def made():
    return [TV("A").__module__, TVT("B").__module__, PS("C").__module__, TAT("Y", int).__module__]
here = __name__
assert_eq([T.__module__, Ts.__module__, P.__module__, X.__module__], ["typing", "typing", "typing", here])
assert_eq(made(), [here] * 4)
ns = {"__name__": "elsewhere", "TV": TV, "TAT": TAT}
exec("r = [TV('D').__module__, TAT('Z', int).__module__]", ns)
assert_eq(ns["r"], ["elsewhere", "elsewhere"])
class A: pass
def names():
    out = []
    for g in (lambda: TV(A()), lambda: TAT(A(), int), lambda: TV(5), lambda: TV(list[int])):
        try: g()
        except TypeError as e: out.append(str(e))
    return out
assert_eq(names(), ["typevar() argument 'name' must be str, not A", "typealias() argument 'name' must be str, not A",
                    "typevar() argument 'name' must be str, not int", "typevar() argument 'name' must be str, not types.GenericAlias"])
