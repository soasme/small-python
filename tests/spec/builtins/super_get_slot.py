# spec: PLS-315 20.3.2, 7.3.6, 16.4.2
# description: super is a non-data descriptor through its slot
# super.__get__: an unbound super binds to an instance, a subclass's
# instance by calling that subclass, a bound one or None gives itself, and
# its explicit calls check their arguments. A subclass defining __set__
# is a data descriptor, so a metaclass's instance of it answers before
# type's own attribute, __prepare__ too; a class statement reads it.
from harness import *
log = []
class A: pass
class B(A): pass
class Sup(super):
    def __init__(self, *args):
        for _ in (): pass
        log.append(len(args)); super().__init__(*args)
class DataSup(super):
    def __set__(self, owner, value): pass
get, unbound, b = super.__get__, super(A), B()
assert_eq(["__get__" in vars(super), type(get).__name__, get.__qualname__, get.__objclass__ is super],
          [True, "wrapper_descriptor", "super.__get__", True])
assert_eq(repr(get), "<slot wrapper '__get__' of 'super' objects>")
assert_eq(repr(unbound.__get__).split(" of ")[0], "<method-wrapper '__get__'")
def errors():
    out = []
    for call in (lambda: get(), lambda: get(1, b), lambda: get(unbound), lambda: get(unbound, b, B, 4),
                 lambda: get(unbound, None, None), lambda: get(unbound, None), lambda: get(unbound, obj=b), lambda: get(unbound, 3)):
        try: call()
        except TypeError as e: out.append(str(e))
    return out
assert_eq(errors(), ["descriptor '__get__' of 'super' object needs an argument",
                     "descriptor '__get__' requires a 'super' object but received a 'int'",
                     "__get__ expected at least 1 argument, got 0", "__get__ expected at most 2 arguments, got 3",
                     "__get__(None, None) is invalid", "__get__(None, None) is invalid",
                     "wrapper __get__() takes no keyword arguments",
                     "super(type, obj): obj (instance of int) is not an instance or subtype of type (A)."])
def binds():
    sup = Sup(A)
    bound = [get(unbound, b), unbound.__get__(b, B), get(sup, b), sup.__get__(b), list(map(get, [sup], [b]))[0]]
    same = [get(super(A, b), 5).__self__ is b, sup.__get__(None, B) is sup]
    return [type(x).__name__ for x in bound], [x.__self__ is b for x in bound], same, log
assert_eq(binds(), (["super", "super", "Sup", "Sup", "Sup"], [True] * 5, [True, True], [1, 2, 2, 2]))
class MetaMeta(type):
    __prepare__ = DataSup(type)
    mro_like = DataSup(type)
Meta = MetaMeta("Meta", (type,), {})
assert_eq([type(Meta.__prepare__).__name__, Meta.__prepare__.__self__ is Meta, type(Meta.mro_like).__name__], ["DataSup", True, "DataSup"])
class Holder:
    data, plain = DataSup(object), Sup(object)
held = Holder()
held.__dict__.update(data="own", plain="own")
assert_eq([type(held.data).__name__, held.plain], ["DataSup", "own"])
class Entries:
    __mro_entries__ = Sup(A)
def statements():
    out = []
    try:
        class FromEntries(Entries()): pass
    except TypeError as e: out.append(str(e))
    try:
        class Generic[T](Entries()): pass
    except TypeError as e: out.append(str(e))
    try:
        class Prepared(metaclass=Meta): pass
    except TypeError as e: out.append(str(e))
    try:
        class GenericPrepared[T](metaclass=Meta): pass
    except TypeError as e: out.append(str(e))
    return out
assert_eq(statements(), ["super(type, obj): obj (instance of Entries) is not an instance or subtype of type (A)."] * 2 +
                        ["'DataSup' object is not callable"] * 2)
