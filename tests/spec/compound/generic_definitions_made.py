# spec: PLS-315 14.15, 16.7, 29.6
# description: a type statement, and a generic function or class, make
# their type parameters in order, each bound in the type parameters'
# scope, the parameters' bounds and defaults and an alias's value lazy;
# a generic function's defaults are evaluated first. The type statement
# stores its alias with StoreName, through a class namespace's Python
# __setitem__ in a class body; the alias's repr is its __qualname__ (or
# TypeAliasType's qualname argument) and its __name__ the name. Inside
# functions, in class bodies and at module level, with no call in the
# body around them.
from harness import *

log = []

def note(x):
    log.append(x)
    return x

type Plain = int
type Pair[K, V: int = str] = dict[K, V]
def ident[T](x: T = note("default")) -> T: return x
class Box[T, *Ts, **P]: pass

assert_eq((repr(Plain), Plain.__name__, Plain.__qualname__, Plain.__type_params__), ("Plain", "Plain", "Plain", ()))
K, V = Pair.__type_params__
assert_eq((repr(Pair), K.__name__, V.__name__, V.__bound__, V.__default__), ("Pair", "K", "V", int, str))
assert_eq(Pair.__value__, dict[K, V])
TypeAliasType = type(Plain)
assert_eq((repr(TypeAliasType("Made", int)), repr(TypeAliasType("Made", int, qualname="Outer.Made"))), ("Made", "Outer.Made"))
assert_eq(([t.__name__ for t in ident.__type_params__], ident()), (["T"], "default"))
assert_eq([type(t).__name__ for t in Box.__type_params__], ["TypeVar", "TypeVarTuple", "ParamSpec"])
assert_eq(log, ["default"])
log.clear()

def made():
    type Local[T] = list[T]
    def local[U](u: U): pass
    class Kept[W]: pass
    return Local, local, Kept

Local, local, Kept = made()
assert_eq((repr(Local), Local.__qualname__, Local.__name__), ("made.<locals>.Local", "made.<locals>.Local", "Local"))
assert_eq((Local.__type_params__[0].__name__, local.__type_params__[0].__name__, Kept.__type_params__[0].__name__),
          ("T", "U", "W"))
assert_eq(Local.__value__, list[Local.__type_params__[0]])

class Namespace(dict):
    def __setitem__(self, key, value):
        log.append(key)
        dict.__setitem__(self, key, value)

class Meta(type):
    @classmethod
    def __prepare__(meta, name, bases): return Namespace()

class Holder(metaclass=Meta):
    type Inner[T] = tuple[T, ...]
    def method[S](self): pass

assert_eq(log, ["__module__", "__qualname__", "__firstlineno__", "Inner", "method", "__static_attributes__",
                "__classdictcell__"])
assert_eq((repr(Holder.Inner), Holder.Inner.__name__, Holder.Inner.__reduce__()), ("Holder.Inner", "Inner", "Inner"))
assert_eq(Holder.method.__type_params__[0].__name__, "S")
