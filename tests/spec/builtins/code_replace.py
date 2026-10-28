# spec: PLS-315 28.2.1, 28.2, 28.1, 16.2
# description: code.replace() of every co_ attribute: argument checks in order, consistency checks, equality, and functions bound by a replaced signature.
from harness import *

FunctionType = type(lambda: None)

def f(a, b=2, *, c=3):
    x = a + b
    return x
co = f.__code__
ints = ["co_argcount", "co_posonlyargcount", "co_kwonlyargcount", "co_nlocals", "co_stacksize", "co_flags", "co_firstlineno"]
byte_fields = ["co_code", "co_linetable", "co_exceptiontable"]
tuples = ["co_consts", "co_names", "co_varnames", "co_freevars", "co_cellvars"]
strs = ["co_filename", "co_name", "co_qualname"]

# Every attribute can be given its own value back; the copy is equal and hashes alike.
for name in ints + byte_fields + tuples + strs:
    same = co.replace(**{name: getattr(co, name)})
    assert_eq(getattr(same, name), getattr(co, name), name)
    assert_true(same == co and hash(same) == hash(co), name)
everything = co.replace(**{name: getattr(co, name) for name in ints + byte_fields + tuples + strs})
assert_true(everything == co and everything is not co)
assert_eq(co.replace(co_argcount=True).co_argcount, 1)
assert_type(co.replace(co_argcount=True).co_argcount, int)

# Argument types.
for name in ints:
    assert_eq(str(assert_raises(TypeError, co.replace, **{name: "x"})), "'str' object cannot be interpreted as an integer")
    assert_eq(str(assert_raises(ValueError, co.replace, **{name: -1})), name + " must be a positive integer")
    assert_eq(str(assert_raises(OverflowError, co.replace, **{name: 2 ** 70})), "Python int too large to convert to C int")
    assert_eq(str(assert_raises(OverflowError, co.replace, **{name: 2 ** 31})), "Python int too large to convert to C int")
for name in byte_fields:
    assert_eq(str(assert_raises(TypeError, co.replace, **{name: "x"})), "replace() argument '%s' must be bytes, not str" % name)
for name in tuples:
    assert_eq(str(assert_raises(TypeError, co.replace, **{name: list(getattr(co, name))})),
              "replace() argument '%s' must be tuple, not list" % name)
for name in strs:
    assert_eq(str(assert_raises(TypeError, co.replace, **{name: 1})), "replace() argument '%s' must be str, not int" % name)
assert_eq(str(assert_raises(TypeError, co.replace, co_bogus=1)), "replace() got an unexpected keyword argument 'co_bogus'")
assert_eq(str(assert_raises(TypeError, co.replace, co_code="s", co_bogus=1)), "replace() got an unexpected keyword argument 'co_bogus'")
assert_raises(TypeError, co.replace, 1)

# Subclasses of str and tuple are accepted.
S = type("S", (str,), {})
T = type("T", (tuple,), {})
assert_eq((co.replace(co_name=S("q")).co_name, co.replace(co_consts=T((1,))).co_consts), ("q", (1,)))

# The checks run in parameter order, whatever the keyword order.
assert_eq(str(assert_raises(TypeError, co.replace, co_varnames=[1], co_argcount="x")), "'str' object cannot be interpreted as an integer")
assert_eq(str(assert_raises(TypeError, co.replace, co_name=1, co_code="s")), "replace() argument 'co_code' must be bytes, not str")
assert_eq(str(assert_raises(TypeError, co.replace, co_flags=-1, co_code="s")), "replace() argument 'co_code' must be bytes, not str")
assert_eq(str(assert_raises(ValueError, co.replace, co_flags=-1, co_argcount=-1)), "co_argcount must be a positive integer")
assert_eq(str(assert_raises(ValueError, co.replace, co_firstlineno=-1, co_stacksize=-1)), "co_stacksize must be a positive integer")
assert_eq(str(assert_raises(ValueError, co.replace, co_stacksize=-1, co_nlocals=-1)), "co_nlocals must be a positive integer")
assert_eq(str(assert_raises(ValueError, co.replace, co_posonlyargcount=3, co_kwonlyargcount=-1)), "co_kwonlyargcount must be a positive integer")

# Consistency: positional-only within positional, enough local names, co_nlocals matching, names all str.
assert_raises(SystemError, co.replace, co_posonlyargcount=3)
assert_raises(SystemError, co.replace, co_posonlyargcount=10, co_argcount=9)
assert_raises(SystemError, co.replace, co_posonlyargcount=3, co_nlocals=1)
too_small = "code: co_varnames is too small"
assert_eq(str(assert_raises(ValueError, co.replace, co_argcount=99)), too_small)
assert_eq(str(assert_raises(ValueError, co.replace, co_kwonlyargcount=99)), too_small)
assert_eq(str(assert_raises(ValueError, co.replace, co_argcount=9, co_nlocals=1)), too_small)
assert_eq(str(assert_raises(ValueError, co.replace, co_varnames=(1, 2))), too_small)
assert_eq(str(assert_raises(ValueError, co.replace, co_flags=co.co_flags | 0x4 | 0x8)), too_small)
assert_eq(str(assert_raises(ValueError, co.replace, co_names=(1,), co_argcount=9)), too_small)
mismatch = "code: co_nlocals != len(co_varnames)"
assert_eq(str(assert_raises(ValueError, co.replace, co_nlocals=3)), mismatch)
assert_eq(str(assert_raises(ValueError, co.replace, co_varnames=("a", "b", "c"))), mismatch)
assert_eq(str(assert_raises(ValueError, co.replace, co_nlocals=1, co_names=(1,))), mismatch)
assert_eq(str(assert_raises(ValueError, co.replace, co_varnames=(1, 2, 3, 4, 5))), mismatch)
for name in ["co_names", "co_varnames", "co_freevars", "co_cellvars"]:
    value = (1, 2, 3, 4) if name == "co_varnames" else (1,)
    assert_eq(str(assert_raises(SystemError, co.replace, **{name: value})), "non-string found in code slot")
assert_eq(co.replace(co_varnames=("a", "b", "c"), co_nlocals=3).co_varnames, ("a", "b", "c"))
assert_eq(co.replace(co_kwonlyargcount=2).co_kwonlyargcount, 2)
assert_eq(co.replace(co_flags=co.co_flags | 0x4).co_flags & 0x4, 0x4)
assert_eq(co.replace(co_stacksize=99, co_flags=99, co_firstlineno=0).co_stacksize, 99)

# Changed values are reported, and the copy is no longer equal.
for name, value in [("co_consts", (None, 5)), ("co_names", ("p",)), ("co_freevars", ("z",)), ("co_cellvars", ("z",)),
                    ("co_code", b"\0\0"), ("co_linetable", b"\0"), ("co_exceptiontable", b"\0"),
                    ("co_varnames", ("p", "q", "r", "s")), ("co_argcount", 1), ("co_kwonlyargcount", 2),
                    ("co_posonlyargcount", 1), ("co_flags", co.co_flags | 0x100), ("co_name", "g"), ("co_firstlineno", 1)]:
    changed = co.replace(**{name: value})
    assert_eq(getattr(changed, name), value, name)
    assert_ne(changed, co, name)
    assert_eq(changed.replace(**{name: getattr(co, name)}), co, name)
assert_eq(co.replace(co_name="g").replace(co_qualname="h").co_name, "g")
# The qualified name, file name, and stack size take no part in equality.
for name, value in [("co_qualname", "q"), ("co_filename", "x"), ("co_stacksize", 99)]:
    changed = co.replace(**{name: value})
    assert_eq((getattr(changed, name), changed == co), (value, True), name)
    assert_eq(changed.replace(co_name="g"), co.replace(co_name="g"), name)

# A function of the copy takes its name, qualified name, and code from it.
r = co.replace(co_name="g", co_qualname="q.g")
h = FunctionType(r, {})
assert_eq((h.__code__ is r, h.__name__, h.__qualname__), (True, "g", "q.g"))

# Renamed parameters bind by their new names; the body still sees its own.
f2 = FunctionType(co.replace(co_varnames=("p", "q", "c", "x")), {}, None, (2,), None, {"c": 3})
assert_eq((f2(1, 2), f2(1), f2(p=4, q=5), f2(1, c=0)), (3, 3, 9, 3))
assert_eq(str(assert_raises(TypeError, lambda: f2(a=1))), "f() got an unexpected keyword argument 'a'")
f3 = FunctionType(co.replace(co_varnames=("p", "q", "c", "x")), {})
assert_eq(str(assert_raises(TypeError, f3, 1, 2)), "f() missing 1 required keyword-only argument: 'c'")
assert_eq(str(assert_raises(TypeError, lambda: f3(p=1))), "f() missing 1 required positional argument: 'q'")
assert_eq(str(assert_raises(TypeError, f3)), "f() missing 2 required positional arguments: 'p' and 'q'")
# Swapped names swap the slots.
def diff(a, b): return a - b
swapped = FunctionType(diff.__code__.replace(co_varnames=("b", "a")), {})
assert_eq((swapped(10, 1), swapped(a=10, b=1)), (9, -9))

# Changed counts move parameters between positional, positional-only, and keyword-only.
g = FunctionType(co.replace(co_flags=co.co_flags | 0x4, co_varnames=("a", "b", "c", "rest"), co_nlocals=4), {})
assert_eq(str(assert_raises(TypeError, g, 1, 2, 3, 4)), "f() missing 1 required keyword-only argument: 'c'")
assert_eq(g(1, 2, 3, 4, c=0), 3)
kw = FunctionType(co.replace(co_argcount=1, co_kwonlyargcount=2), {})
assert_eq((kw.__defaults__, kw(5, b=1, c=2)), (None, 6))
assert_eq(str(assert_raises(TypeError, kw, 5, 1)), "f() takes 1 positional argument but 2 were given")
po = FunctionType(co.replace(co_posonlyargcount=1), {}, None, (2,), None, {"c": 3})
assert_eq(str(assert_raises(TypeError, lambda: po(a=1))), "f() got some positional-only arguments passed as keyword arguments: 'a'")
assert_eq(po(1), 3)
both = FunctionType(co.replace(co_flags=co.co_flags | 0x4 | 0x8, co_varnames=("a", "b", "c", "x", "y"), co_nlocals=5), {})
assert_eq(both.__code__.co_varnames, ("a", "b", "c", "x", "y"))
assert_eq(both(1, 2, 9, c=0, z=1), 3)
# A slot past the parameters is the body's local: binding it gives the local a starting value.
def uses(a):
    y = a
    return y
assert_eq(FunctionType(uses.__code__.replace(co_argcount=2), {})(1, 5), 1)

# __code__ assignment keeps the copy and its signature; a later assignment drops it.
def target(a, b=2, *, c=3): return "target"
target.__code__ = co.replace(co_varnames=("p", "q", "c", "x"))
assert_eq(target(p=1, q=2), 3)
target.__code__ = co
assert_eq(target(a=1, b=2), 3)
assert_eq(str(assert_raises(TypeError, lambda: target(p=1))), "target() got an unexpected keyword argument 'p'")

# Lambdas, and the CO_ITERABLE_COROUTINE flag, as before.
lam = lambda first, second: first * 10 + second
assert_eq(FunctionType(lam.__code__.replace(co_varnames=("second", "first")), {})(second=1, first=2), 12)
