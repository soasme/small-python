# spec: PLS-315 29.9.1, 29.5.2, 29.6
# description: storing into or deleting a generic alias's attributes
# fails by the attribute's kind; its __reduce__ rebuilds it, a starred one
# through next(); dir() adds its own names but not the blocked ones. A
# union is not iterable; a type alias iterates to Unpack of itself once.
from harness import *
a, starred = list[int], (*tuple[int],)[0]
def stores():
    out = []
    for name in ("__origin__", "__parameters__", "__name__", "__doc__", "__bases__", "__reduce__", "__class__"):
        for store in (lambda: setattr(a, name, 1), lambda: delattr(a, name)):
            try: store()
            except (AttributeError, TypeError) as e: out.append(str(e))
    return out
tail = "' and no __dict__ for setting new attributes"
assert_eq(stores(), ["readonly attribute"] * 2 + ["attribute '__parameters__' of 'types.GenericAlias' objects is not writable"] * 2
          + ["'types.GenericAlias' object has no attribute '__name__" + tail] * 2
          + ["'types.GenericAlias' object attribute '__doc__' is read-only"] * 2
          + ["'types.GenericAlias' object has no attribute '__bases__" + tail] * 2
          + ["'types.GenericAlias' object attribute '__reduce__' is read-only"] * 2
          + ["__class__ must be set to a class, not 'int' object", "can't delete __class__ attribute"])
function, args = a.__reduce__()
assert_eq((function is type(a), args), (True, (list, (int,))))
function, (it,) = starred.__reduce__()
assert_eq((function is next, list(it)), (True, [starred]))
assert_eq(sorted(set(dir(a)) - set(dir(list))), ["__args__", "__mro_entries__", "__origin__", "__parameters__",
                                                  "__typing_unpacked_tuple_args__", "__unpacked__"])
u = int | str
def unions():
    out = []
    for f in (lambda: iter(u), lambda: 1 in u):
        try: f()
        except TypeError as e: out.append(str(e))
    return out
assert_eq(unions(), ["'typing.Union' object is not iterable", "argument of type 'typing.Union' is not a container or iterable"])
type X = int
assert_eq([repr(v) for v in X], ["typing.Unpack[X]"])
assert_eq(1 in X, False)
