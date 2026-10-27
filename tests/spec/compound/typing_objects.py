# spec: PLS-315 29.1, 29.5, 29.7, 16.7
# description: The typing intrinsics reached through language constructs: NoDefault, unions, and Generic.
from harness import *

def generic[T, *Ts, **P](): pass
T, Ts, P = generic.__type_params__
home = qualified(type(T)).rpartition(".")[0]
def named(name):
    return f"{home}.{name}" if home else name

# %NoDefault% marks a parameter without a default.
NoDefault = T.__default__
assert_eq(repr(NoDefault), named("NoDefault"))
assert_eq(type(NoDefault).__name__, "NoDefaultType")
assert_false(T.has_default())
def with_default[U = int](): pass
assert_is(with_default.__type_params__[0].__default__, int)
assert_true(with_default.__type_params__[0].has_default())
assert_is(type(NoDefault)(), NoDefault)
e = assert_raises(TypeError, type(NoDefault), 1)
assert_eq(str(e), "NoDefaultType takes no arguments")
for intrinsic in (type(T), type(Ts), type(P), type(NoDefault)):
    with assert_raises(TypeError):
        class Sub(intrinsic):
            pass

# Unions.
u = int | str
UnionType = type(u)
assert_eq(repr(UnionType), f"<class '{named('Union')}'>")
assert_eq(u.__args__, (int, str))
assert_eq(repr(u), "int | str")
assert_eq(repr(int | None), "int | None")
assert_eq((int | None).__args__, (int, type(None)))
assert_eq(int | str | int, u)
assert_is(int | int, int)
assert_eq(u, str | int)
assert_eq(hash(u), hash(str | int))
assert_eq(((int | str) | (bytes | int)).__args__, (int, str, bytes))
e = assert_raises(TypeError, lambda: int | 1)
assert_eq(str(e), "unsupported operand type(s) for |: 'type' and 'int'")
assert_eq((list[int] | None).__args__, (list[int], type(None)))
assert_eq((T | int).__parameters__, (T,))
assert_eq((T | int)[str], str | int)
e = assert_raises(TypeError, lambda: u[int])
assert_eq(str(e), "int | str is not a generic class")
assert_true(isinstance(1, int | str))
assert_true(isinstance(None, int | None))
assert_false(isinstance(1.0, int | str))
assert_true(issubclass(bool, int | str))
# Members are tried in order, so a generic alias after an accepting member is not reached.
assert_true(isinstance(1, int | list[int]))
e = assert_raises(TypeError, isinstance, "x", int | list[int])
assert_eq(str(e), "isinstance() argument 2 cannot be a parameterized generic")
e = assert_raises(TypeError, UnionType)
assert_eq(str(e), f"cannot create '{named('Union')}' instances")
assert_eq(UnionType[int, str], int | str)
assert_eq(repr(UnionType[int, None]), "int | None")
with assert_raises(TypeError):
    class SubUnion(UnionType):
        pass

# Generic: a class with type parameters gets Generic[params] in its bases.
class Box[X]:
    pass
Generic = Box.__mro__[1]
assert_eq(Box.__mro__, (Box, Generic, object))
assert_eq(repr(Generic), f"<class '{named('Generic')}'>")
assert_eq(Box.__type_params__, Box.__parameters__)
assert_eq(len(Box.__parameters__), 1)
alias = Box[int]
assert_is(alias.__origin__, Box)
assert_eq(alias.__args__, (int,))
e = assert_raises(TypeError, lambda: Box[int, str])
assert_eq(str(e), f"Too many arguments for {Box!r}; actual 2, expected 1")
class Pair[A, B]: pass
e = assert_raises(TypeError, lambda: Pair[int])
assert_eq(str(e), f"Too few arguments for {Pair!r}; actual 1, expected at least 2")
class Defaulted[A, B=int]: pass
assert_eq(Defaulted[str].__args__, (str, int))
e = assert_raises(TypeError, lambda: Defaulted[()])
assert_eq(str(e), f"Too few arguments for {Defaulted!r}; actual 0, expected at least 1")
# Generic[...] as an explicit base.
class Explicit(Generic[T]):
    pass
assert_eq(Explicit.__parameters__, (T,))
assert_eq(Explicit.__mro__, (Explicit, Generic, object))
class Derived(Box[int]):
    pass
assert_eq(Derived.__mro__, (Derived, Box, Generic, object))
e = assert_raises(TypeError, lambda: Generic[int])
assert_eq(str(e), "Parameters to Generic[...] must all be type variables or parameter specification variables.")
with assert_raises(TypeError, message="Cannot inherit from Generic[...] multiple times."):
    class Twice(Generic[T], Generic[P]):
        pass
assert_type(Generic(), Generic)
with assert_raises(TypeError, message="Cannot inherit from plain Generic"):
    class Sub(Generic):
        pass
