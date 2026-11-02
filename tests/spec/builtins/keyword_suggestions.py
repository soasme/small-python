# spec: PLS-315 7.4.3, 7.4.4, 7.4.5, 21.3.2
# description: a keyword naming no parameter is reported with the closest keyword parameter name.
from harness import *

def message(call, *args, **kwargs):
    return str(assert_raises(TypeError, call, *args, **kwargs))

# Functions suggest among positional-or-keyword and keyword-only parameters.
def f(blech=None, /, aaa=None, *args, late1=None, **_):
    pass
def g(blech=None, /, aaa=None, *args, late1=None):
    pass
assert_eq(message(g, aa=1), "g() got an unexpected keyword argument 'aa'. Did you mean 'aaa'?")
assert_eq(message(g, late11=1), "g() got an unexpected keyword argument 'late11'. Did you mean 'late1'?")
assert_eq(message(g, blach=1), "g() got an unexpected keyword argument 'blach'")
assert_eq(message(g, orgs=1), "g() got an unexpected keyword argument 'orgs'")
def kinds(BLuch=None, Luch=None, fluch=None):
    pass
assert_eq(message(kinds, luch=1), "kinds() got an unexpected keyword argument 'luch'. Did you mean 'Luch'?")
def close(blach=None, bluchi=None):
    pass
assert_eq(message(close, bluch=1), "close() got an unexpected keyword argument 'bluch'. Did you mean 'blach'?")
def cafe(café=None):
    pass
assert_eq(message(cafe, cafe=1), "cafe() got an unexpected keyword argument 'cafe'. Did you mean 'café'?")
assert_eq(message(lambda *, key: 1, kye=1), "<lambda>() got an unexpected keyword argument 'kye'")
long = "a" * 41
scope = {}
exec(f"def far(x{long}x=1): pass", scope)
assert_eq(message(scope["far"], **{f"y{long}y": 1}), f"far() got an unexpected keyword argument 'y{long}y'")
exec(f"def near(x{long}=1): pass", scope)
assert_eq(message(scope["near"], **{f"y{long}": 1}), f"near() got an unexpected keyword argument 'y{long}'. Did you mean 'x{long}'?")
for n, near in ((749, ". Did you mean 'a1'?"), (750, "")):
    scope = {}
    exec("def wide(" + ", ".join(f"a{i}" for i in range(n)) + "): pass", scope)
    assert_eq(message(scope["wide"], a1x=1), "wide() got an unexpected keyword argument 'a1x'" + near)

# Built-ins suggest among their keyword parameters.
assert_eq(message(print, sepp=1), "print() got an unexpected keyword argument 'sepp'. Did you mean 'sep'?")
assert_eq(message(round, 1, ndigit=1), "round() got an unexpected keyword argument 'ndigit'. Did you mean 'ndigits'?")
assert_eq(message("a".split, maxsplt=1), "split() got an unexpected keyword argument 'maxsplt'. Did you mean 'maxsplit'?")
assert_eq(message(sorted, [], kee=1), "sort() got an unexpected keyword argument 'kee'. Did you mean 'key'?")
assert_eq(message(max, [1], defalt=1), "max() got an unexpected keyword argument 'defalt'. Did you mean 'default'?")
assert_eq(message(property, fgett=1), "property() got an unexpected keyword argument 'fgett'. Did you mean 'fget'?")
assert_eq(message(zip, [], strct=True), "zip() got an unexpected keyword argument 'strct'. Did you mean 'strict'?")
assert_eq(message(sentinel, "s", rpr="x"), "sentinel() got an unexpected keyword argument 'rpr'. Did you mean 'repr'?")
assert_eq(message(f.__code__.replace, co_nme="x"), "replace() got an unexpected keyword argument 'co_nme'. Did you mean 'co_name'?")
assert_eq(message(NameError, nme="x"), "NameError() got an unexpected keyword argument 'nme'. Did you mean 'name'?")
assert_eq(message(ImportError, pth="x"), "ImportError() got an unexpected keyword argument 'pth'. Did you mean 'path'?")
assert_eq(message(print, zzzz=1), "print() got an unexpected keyword argument 'zzzz'")

# A str subclass key is matched by equality.
class S(str):
    pass
assert_eq(f.__code__.replace(**{S("co_name"): "x"}).co_name, "x")
assert_eq(repr(sentinel("s", **{S("repr"): "x"})), "x")
assert_eq(NameError(**{S("name"): "x"}).name, "x")
class Equal(str):
    def __eq__(self, other):
        return True
    def __hash__(self):
        return str.__hash__(self) ^ 3
for call in (lambda k: print(0, **k), lambda k: round(1, **k), lambda k: sorted([], **k), lambda k: property(**k),
             lambda k: min([1], **k), lambda k: sentinel("s", **k), lambda k: f.__code__.replace(**k)):
    assert_true(message(call, {Equal("foo"): 1}).startswith("invalid keyword argument for "))
assert_eq(message(lambda: print(**{Equal("foo"): 1, "zzz": 2})), "print() got an unexpected keyword argument 'zzz'")
assert_eq(message(lambda: zip([], **{Equal("foo"): 1})), "zip() got an unexpected keyword argument 'foo'")
assert_eq(message(lambda: NameError(**{Equal("foo"): 1})), "NameError() got an unexpected keyword argument 'foo'")
assert_eq((lambda a=0: a)(**{Equal("foo"): 5}), 5)
class Raising(str):
    def __eq__(self, other):
        raise KeyError(other)
    def __hash__(self):
        return 1
assert_raises(KeyError, lambda: print(**{Raising("foo"): 1}))
